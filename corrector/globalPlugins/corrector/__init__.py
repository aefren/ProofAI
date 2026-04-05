import threading

import addonHandler
import api
import brailleInput
import config
import controlTypes
import globalPluginHandler
import gui
import textInfos
import ui
import wx
from logHandler import log
from scriptHandler import script

from . import configspec
from .client import OpenAICompatibleClient, ProofreadingError


addonHandler.initTranslation()

conf = config.conf["proofai"]


def is_editable_focus_object(obj):
	if not obj:
		return False
	states = getattr(obj, "states", set())
	return (
		controlTypes.State.FOCUSED in states
		and (
			controlTypes.State.EDITABLE in states
			or controlTypes.State.MULTILINE in states
		)
	)


def get_selected_text_from_focus():
	obj = api.getFocusObject()
	if not is_editable_focus_object(obj):
		return None, ""
	if not hasattr(obj, "makeTextInfo"):
		return obj, ""
	try:
		selection = obj.makeTextInfo(textInfos.POSITION_SELECTION)
	except Exception:
		return obj, ""
	return obj, (selection.text or "")


class SettingsDlg(gui.settingsDialogs.SettingsPanel):

	title = _("ProofAI")

	def makeSettings(self, settingsSizer):
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		self.apiKey = sHelper.addLabeledControl(
			_("API &key:"),
			wx.TextCtrl,
			style=wx.TE_PASSWORD,
		)
		self.apiKey.SetValue(conf["apiKey"])

		self.endpoint = sHelper.addLabeledControl(
			_("&Endpoint URL:"),
			wx.TextCtrl,
		)
		self.endpoint.SetValue(conf["endpoint"])

		self.model = sHelper.addLabeledControl(
			_("&Model:"),
			wx.TextCtrl,
		)
		self.model.SetValue(conf["model"])

		self.timeout = sHelper.addLabeledControl(
			_("&Timeout (seconds):"),
			wx.SpinCtrl,
			min=10,
			max=300,
		)
		self.timeout.SetValue(conf["timeout"])

		self.systemPrompt = sHelper.addLabeledControl(
			_("&Proofreading prompt:"),
			wx.TextCtrl,
			style=wx.TE_MULTILINE,
		)
		self.systemPrompt.SetMinSize((0, 140))
		self.systemPrompt.SetValue(conf["systemPrompt"])

		self.announceSuccess = sHelper.addItem(
			wx.CheckBox(
				self,
				label=_("&Announce when proofreading finishes"),
			)
		)
		self.announceSuccess.SetValue(conf["announceSuccess"])

	def onSave(self):
		conf["apiKey"] = self.apiKey.GetValue().strip()
		conf["endpoint"] = self.endpoint.GetValue().strip()
		conf["model"] = self.model.GetValue().strip()
		conf["timeout"] = self.timeout.GetValue()
		conf["systemPrompt"] = self.systemPrompt.GetValue().strip() or configspec.DEFAULT_SYSTEM_PROMPT
		conf["announceSuccess"] = self.announceSuccess.GetValue()


class ProofreadingThread(threading.Thread):

	def __init__(self, plugin, text):
		super().__init__(daemon=True)
		self.plugin = plugin
		self.text = text

	def run(self):
		try:
			client = OpenAICompatibleClient(
				endpoint=conf["endpoint"],
				api_key=conf["apiKey"],
				model=conf["model"],
				system_prompt=conf["systemPrompt"],
				timeout=conf["timeout"],
			)
			corrected_text = client.proofread_text(self.text)
			wx.CallAfter(self.plugin.onProofreadingSuccess, corrected_text)
		except ProofreadingError as exc:
			wx.CallAfter(self.plugin.onProofreadingFailure, str(exc))
		except Exception as exc:
			log.exception("An unexpected error occurred while proofreading the selected text")
			wx.CallAfter(self.plugin.onProofreadingFailure, str(exc))


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	scriptCategory = _("ProofAI")

	def __init__(self):
		super().__init__()
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(SettingsDlg)
		self._isProcessing = False
		self._targetWindowHandle = None

	def terminate(self):
		try:
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(SettingsDlg)
		except ValueError:
			pass
		super().terminate()

	def _validate_configuration(self):
		if not conf["apiKey"].strip():
			ui.message(_("Set the API key in ProofAI settings first"))
			return False
		if not conf["endpoint"].strip():
			ui.message(_("Set the endpoint URL in ProofAI settings first"))
			return False
		if not conf["model"].strip():
			ui.message(_("Set the model in ProofAI settings first"))
			return False
		return True

	def startProofreading(self):
		if self._isProcessing:
			ui.message(_("A proofreading request is already in progress"))
			return
		if not self._validate_configuration():
			return
		text = ""
		try:
			focus_obj, text = get_selected_text_from_focus()
		except Exception:
			log.exception("Could not retrieve the selected text")
			ui.message(_("Could not retrieve the selected text"))
			return
		if not is_editable_focus_object(focus_obj):
			ui.message(_("You must select text in an edit field"))
			return
		if not text or not text.strip():
			ui.message(_("You must select text in an edit field"))
			return
		self._targetWindowHandle = getattr(focus_obj, "windowHandle", None)
		self._isProcessing = True
		ui.message(_("Proofreading selected text"))
		ProofreadingThread(self, text).start()

	def onProofreadingSuccess(self, corrected_text):
		self._isProcessing = False
		focus_obj = api.getFocusObject()
		if (
			not is_editable_focus_object(focus_obj)
			or getattr(focus_obj, "windowHandle", None) != self._targetWindowHandle
		):
			ui.message(_("Proofreading finished, but the focus changed so the selection could not be replaced"))
			return
		try:
			brailleInput.handler.sendChars(corrected_text)
		except Exception:
			log.exception("Could not insert the proofread text")
			ui.message(_("Proofreading finished, but the proofread text could not be inserted"))
			return
		if conf["announceSuccess"]:
			ui.message(_("Text proofread and inserted"))

	def onProofreadingFailure(self, error_message):
		self._isProcessing = False
		ui.message(_("Proofreading failed: %s") % error_message)

	@script(
		gesture="kb:nvda+shift+x",
		description=_("Proofreads the selected text in the active edit field"),
	)
	def script_proofreadSelection(self, gesture):
		self.startProofreading()
