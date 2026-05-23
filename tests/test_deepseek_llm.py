import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from courseweaver.llm import DeepSeekClient, KimiClient, LLMError, create_llm_client, load_api_key
from courseweaver.models import KnowledgeUnit, NoteChunk
from courseweaver.notes import _rewrite_messages, refine_note_chunks_with_llm


class LLMClientTests(unittest.TestCase):
    def test_builds_openai_compatible_chat_request(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=None)
        response.read.return_value = json.dumps(
            {"choices": [{"message": {"content": "改写后的讲义"}}]}
        ).encode("utf-8")

        with patch("urllib.request.urlopen", return_value=response) as urlopen:
            client = DeepSeekClient(api_key="test-key", model="deepseek-v4-pro", timeout=3)
            content = client.chat(
                [
                    {"role": "system", "content": "你是助教。"},
                    {"role": "user", "content": "请改写。"},
                ],
                max_tokens=800,
            )

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))

        self.assertEqual(content, "改写后的讲义")
        self.assertEqual(request.full_url, "https://api.deepseek.com/chat/completions")
        self.assertEqual(request.headers["Authorization"], "Bearer test-key")
        self.assertEqual(payload["model"], "deepseek-v4-pro")
        self.assertEqual(payload["thinking"], {"type": "disabled"})
        self.assertEqual(payload["stream"], False)

    def test_builds_kimi_chat_request(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=None)
        response.read.return_value = json.dumps(
            {"choices": [{"message": {"content": "Kimi 改写"}}]}
        ).encode("utf-8")

        with patch("urllib.request.urlopen", return_value=response) as urlopen:
            client = KimiClient(api_key="moonshot-key", model="kimi-k2.6", timeout=3)
            content = client.chat(
                [
                    {"role": "system", "content": "你是助教。"},
                    {"role": "user", "content": "请改写。"},
                ],
                max_tokens=900,
            )

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))

        self.assertEqual(content, "Kimi 改写")
        self.assertEqual(request.full_url, "https://api.moonshot.ai/v1/chat/completions")
        self.assertEqual(request.headers["Authorization"], "Bearer moonshot-key")
        self.assertEqual(payload["model"], "kimi-k2.6")
        self.assertEqual(payload["max_completion_tokens"], 900)
        self.assertNotIn("thinking", payload)

    def test_requires_api_key(self):
        with self.assertRaises(LLMError):
            DeepSeekClient(api_key="")

    def test_loads_named_api_key_from_dotenv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dotenv = Path(tmpdir) / ".env"
            dotenv.write_text("DEEPSEEK_API_KEY=abc123\n", encoding="utf-8")

            self.assertEqual(load_api_key("DEEPSEEK_API_KEY", dotenv), "abc123")

    def test_loads_raw_dotenv_value_as_deepseek_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dotenv = Path(tmpdir) / ".env"
            dotenv.write_text("sk-raw-value\n", encoding="utf-8")

            self.assertEqual(load_api_key("DEEPSEEK_API_KEY", dotenv), "sk-raw-value")
            self.assertEqual(load_api_key("MOONSHOT_API_KEY", dotenv), "")

    def test_environment_variable_wins_over_dotenv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dotenv = Path(tmpdir) / ".env"
            dotenv.write_text("DEEPSEEK_API_KEY=from-file\n", encoding="utf-8")
            with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "from-env"}):
                self.assertEqual(load_api_key("DEEPSEEK_API_KEY", dotenv), "from-env")

    def test_creates_provider_clients(self):
        self.assertIsInstance(create_llm_client("deepseek", api_key="k"), DeepSeekClient)
        self.assertIsInstance(create_llm_client("kimi", api_key="k"), KimiClient)
        with self.assertRaises(LLMError):
            create_llm_client("unknown", api_key="k")


class DeepSeekNoteRefinementTests(unittest.TestCase):
    def test_refines_note_chunk_content_but_preserves_source_mapping(self):
        units = [
            KnowledgeUnit(
                unit_id="U_0001",
                name="Maximum Likelihood Estimation",
                unit_type="concept",
                summary="MLE maximizes likelihood.",
                source_pages=[6],
                source_blocks=["p006_b001"],
                importance="core",
            )
        ]
        chunks = [
            NoteChunk(
                chunk_id="N_0001",
                note_file="01_lecture_notes.md",
                section_title="Maximum Likelihood Estimation",
                content="旧内容",
                source_units=["U_0001"],
                source_blocks=["p006_b001"],
            )
        ]
        client = Mock()
        client.chat.return_value = "## Maximum Likelihood Estimation [p.6]\n\n自然讲义内容\n\n来源：p.6"

        refined = refine_note_chunks_with_llm(chunks, units, client)

        self.assertIn("自然讲义内容", refined[0].content)
        self.assertEqual(refined[0].source_units, ["U_0001"])
        self.assertEqual(refined[0].source_blocks, ["p006_b001"])

    def test_rewrite_prompt_avoids_fixed_note_template(self):
        unit = KnowledgeUnit(
            unit_id="U_0001",
            name="Maximum Likelihood Estimation",
            unit_type="concept",
            summary="MLE maximizes likelihood.",
            source_pages=[6],
            source_blocks=["p006_b001"],
            importance="core",
        )
        chunk = NoteChunk(
            chunk_id="N_0001",
            note_file="01_lecture_notes.md",
            section_title="Maximum Likelihood Estimation",
            content="旧内容",
            source_units=["U_0001"],
            source_blocks=["p006_b001"],
        )

        prompt = _rewrite_messages(chunk, [unit])[1]["content"]

        self.assertIn("不要每一节都使用同样的小标题", prompt)
        self.assertIn("符号含义 -> 推导为什么成立 -> 结论怎么用", prompt)
        self.assertNotIn("先讲问题和动机，再讲直觉", prompt)


if __name__ == "__main__":
    unittest.main()
