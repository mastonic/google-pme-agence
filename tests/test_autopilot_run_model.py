import unittest

from backend.models.database import AutomationRun, AgentTeamRun


class AutopilotRunModelTests(unittest.TestCase):
    def test_autopilot_progress_fields_live_on_automation_run(self):
        for field in [
            "current_business_id",
            "current_business_name",
            "current_stage",
            "current_index",
            "total_selected",
            "heartbeat_at",
        ]:
            self.assertTrue(hasattr(AutomationRun, field), field)

    def test_agent_team_run_does_not_carry_autopilot_progress_fields(self):
        self.assertFalse(hasattr(AgentTeamRun, "heartbeat_at"))
        self.assertFalse(hasattr(AgentTeamRun, "current_stage"))


if __name__ == "__main__":
    unittest.main()
