import unittest

from aiohttp import web

from src.fetchers.base import Article
from src.pushers.feishu import FeishuPusher


class FeishuPusherTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.received_payload = None

        async def handle(request):
            self.received_payload = await request.json()
            return web.json_response({"code": 0, "msg": "success"})

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

        pushed = await FeishuPusher(self.webhook_url).push([article])

        self.assertTrue(pushed)
        self.assertEqual(self.received_payload["msg_type"], "post")
        zh_cn = self.received_payload["content"]["post"]["zh_cn"]
        self.assertIn("Horizon AI", zh_cn["title"])
        self.assertEqual(zh_cn["content"][1][0]["tag"], "a")
        self.assertEqual(zh_cn["content"][1][0]["href"], article.url)


if __name__ == "__main__":
    unittest.main()
