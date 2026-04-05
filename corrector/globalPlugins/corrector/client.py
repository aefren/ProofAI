import addonHandler
import json
import socket
from urllib import error, request

addonHandler.initTranslation()

class ProofreadingError(Exception):
	pass


class OpenAICompatibleClient:

	def __init__(self, endpoint, api_key, model, system_prompt, timeout):
		self.endpoint = endpoint
		self.api_key = api_key
		self.model = model
		self.system_prompt = system_prompt
		self.timeout = timeout

	def proofread_text(self, text):
		payload = {
			"model": self.model,
			"temperature": 0,
			"messages": [
				{"role": "system", "content": self.system_prompt},
				{"role": "user", "content": text},
			],
		}
		headers = {
			"Content-Type": "application/json",
		}
		if self.api_key:
			headers["Authorization"] = f"Bearer {self.api_key}"
		req = request.Request(
			self.endpoint,
			data=json.dumps(payload).encode("utf-8"),
			headers=headers,
			method="POST",
		)
		try:
			with request.urlopen(req, timeout=self.timeout) as response:
				data = json.loads(response.read().decode("utf-8"))
		except error.HTTPError as exc:
			raise ProofreadingError(self._extract_http_error(exc)) from exc
		except error.URLError as exc:
			raise ProofreadingError(_("Connection error: %s") % exc.reason) from exc
		except (TimeoutError, socket.timeout) as exc:
			raise ProofreadingError(_("The request to the API timed out")) from exc
		except Exception as exc:
			raise ProofreadingError(str(exc)) from exc

		content = self._extract_content(data)
		if not content:
			raise ProofreadingError(_("The API did not return any proofread text"))
		return content

	def _extract_http_error(self, exc):
		try:
			raw = exc.read().decode("utf-8", errors="replace")
			data = json.loads(raw)
			message = data.get("error", {}).get("message")
			if message:
				return message
			return raw or f"HTTP {exc.code}"
		except Exception:
			return f"HTTP {exc.code}"

	def _extract_content(self, data):
		choices = data.get("choices") or []
		if not choices:
			return ""
		message = choices[0].get("message") or {}
		content = message.get("content", "")
		if isinstance(content, str):
			return content.strip()
		if isinstance(content, list):
			parts = []
			for item in content:
				if isinstance(item, dict) and item.get("type") == "text":
					parts.append(item.get("text", ""))
			return "".join(parts).strip()
		return str(content).strip()
