import addonHandler
import config

addonHandler.initTranslation()

DEFAULT_SYSTEM_PROMPT = _(
	"You are an orthography and grammar proofreader. "
	"Correct the user's text while preserving its original language, tone, "
	"line breaks, and formatting. "
	"Return only the corrected text, with no comments or explanations."
)


confSpecs = {
	"apiKey": "string(default='')",
	"endpoint": "string(default='https://api.openai.com/v1/chat/completions')",
	"model": "string(default='gpt-4.1-mini')",
	"systemPrompt": f"string(default={DEFAULT_SYSTEM_PROMPT!r})",
	"timeout": "integer(min=10, max=300, default=60)",
	"announceSuccess": "boolean(default=True)",
}


config.conf.spec["proofai"] = confSpecs
