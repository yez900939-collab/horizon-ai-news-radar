import unittest

from aiohttp import web

from src.fetchers.base import Article
from src.pushers.feishu import FeishuPusher


class FeishuPusherTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.received_payload = None
        self.received_payloads = []
        self.response_payload = {"code": 0, "msg": "success"}

        async def handle(request):
            self.received_payload = await request.json()
            self.received_payloads.append(self.received_payload)
            return web.json_response(self.response_payload)

        app = web.Application()
        app.router.add_post("/hook", handle)
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "127.0.0.1", 0)
        await self.site.start()
        port = self.site._server.sockets[0].getsockname()[1]
        self.webhook_url = f"http://127.0.0.1:{port}/hook"

    async def asyncTearDown(self):
        await self.runner.cleanup()

    async def test_pushes_daily_digest_as_feishu_rich_text(self):
        article = Article(
            title="Critical AI security update",
            url="https://example.com/update",
            source="example",
            summary="一项值得关注的 AI 安全更新。",
            importance=5,
        )

        pusher = FeishuPusher(self.webhook_url, signing_secret="demo")
        pushed = await pusher.push([article])

        self.assertTrue(pushed)
        self.assertEqual(self.received_payload["msg_type"], "post")
        timestamp = self.received_payload["timestamp"]
        self.assertEqual(
            self.received_payload["sign"],
            pusher.generate_signature("demo", timestamp),
        )
        zh_cn = self.received_payload["content"]["post"]["zh_cn"]
        self.assertIn("Horizon 网络安全精选", zh_cn["title"])
        self.assertEqual(zh_cn["content"][1][0]["tag"], "a")
        self.assertEqual(zh_cn["content"][1][0]["href"], article.url)

    def test_generates_feishu_signature_from_timestamp_and_secret(self):
        signature = FeishuPusher.generate_signature("demo", 1599360473)

        self.assertEqual(
            signature,
            "l1N0gAcBjdwBvGm1xMjOF0XSyaLRpR7tuO5dHfhAYc8=",
        )

    async def test_raises_when_feishu_rejects_the_message(self):
        self.response_payload = {
            "code": 19021,
            "msg": "sign match fail",
        }
        article = Article(
            title="New reasoning model launch",
            url="https://example.com/ai",
            source="ai-lab",
            summary="新推理模型发布。",
            importance=5,
        )

        with self.assertRaisesRegex(RuntimeError, "19021"):
            await FeishuPusher(self.webhook_url).push([article])

    async def test_pushes_ai_and_cybersecurity_as_separate_digests(self):
        articles = [
            Article(
                title="New reasoning model launch",
                url="https://example.com/ai",
                source="ai-lab",
                summary="新推理模型发布。",
                importance=5,
            ),
            Article(
                title="CVE-2026-1234 critical RCE vulnerability",
                url="https://example.com/cve",
                source="security-feed",
                summary="关键远程代码执行漏洞。",
                importance=5,
            ),
        ]

        await FeishuPusher(self.webhook_url).push(articles)

        self.assertEqual(len(self.received_payloads), 2)
        titles = [
            payload["content"]["post"]["zh_cn"]["title"]
            for payload in self.received_payloads
        ]
        self.assertTrue(any("AI 精选" in title for title in titles))
        self.assertTrue(any("网络安全精选" in title for title in titles))

    async def test_ai_only_channel_excludes_cybersecurity_digest(self):
        articles = [
            Article(
                title="New reasoning model launch",
                url="https://example.com/ai",
                source="ai-lab",
                summary="新推理模型发布。",
                importance=5,
            ),
            Article(
                title="CVE-2026-1234 critical RCE vulnerability",
                url="https://example.com/cve",
                source="security-feed",
                summary="关键远程代码执行漏洞。",
                importance=5,
            ),
        ]

        await FeishuPusher(self.webhook_url, include_security=False).push(articles)

        self.assertEqual(len(self.received_payloads), 1)
        title = self.received_payloads[0]["content"]["post"]["zh_cn"]["title"]
        self.assertIn("AI 精选", title)
        self.assertNotIn("网络安全", title)
        self.assertNotIn("sign", self.received_payloads[0])


if __name__ == "__main__":
    unittest.main()
