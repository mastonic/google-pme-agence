from crewai.tools import BaseTool

class GmailDraftTool(BaseTool):
    name: str = "Gmail Draft Generator"
    description: str = "Generates email drafts in Gmail"

    def _run(self, content: str) -> str:
        return f"Created draft with content: {content}"
