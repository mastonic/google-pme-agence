import unittest

from backend.agents.manager import LocalPulseManager, PROVIDERS, PROVIDERS_TEXT


class ProviderChainTests(unittest.TestCase):
    def test_latest_gemini_chain_has_no_25(self):
        names=[p["name"] for p in PROVIDERS_TEXT]
        self.assertEqual(names[0], "gemini-3.8-flash")
        self.assertIn("gemini-3.7-flash", names)
        self.assertIn("gemini-3.6-flash", names)
        self.assertIn("gemini-3.5-flash-lite", names)
        self.assertNotIn("gemini-2.5-flash", names)

    def test_unavailable_model_is_classified_for_fallback(self):
        m=LocalPulseManager.__new__(LocalPulseManager)
        kind=m._provider_error_kind(Exception("404 model is no longer available"))
        self.assertEqual(kind, "unavailable")

    def test_quota_is_classified_for_fallback(self):
        m=LocalPulseManager.__new__(LocalPulseManager)
        kind=m._provider_error_kind(Exception("429 RESOURCE_EXHAUSTED quota"))
        self.assertEqual(kind, "quota")

    def test_failed_provider_is_cached_for_same_manager_run(self):
        m=LocalPulseManager.__new__(LocalPulseManager)
        m._disabled_providers=set()
        m.log_queue=None
        m.log_buffer=None
        m.redis_client=None
        m.business_id=None
        m.loop=None

        calls=[]
        def fake_call(provider, prompt, max_tokens, system, temperature):
            calls.append(provider["name"])
            if provider["name"]=="gemini-3.8-flash":
                raise Exception("429 quota exceeded")
            return "ok"

        m._call_provider=fake_call
        self.assertEqual(m._call("hello"), "ok")
        first_calls=list(calls)
        calls.clear()
        self.assertEqual(m._call("hello again"), "ok")

        self.assertIn("gemini-3.8-flash", first_calls)
        self.assertNotIn("gemini-3.8-flash", calls)


if __name__ == "__main__":
    unittest.main()
