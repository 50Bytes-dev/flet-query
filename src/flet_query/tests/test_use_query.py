import asyncio
import random
from typing import Any
import flet as ft
from flet_query.query import QueryStatus
from flet_query.hooks.use_query import use_query


async def get_posts(search_text: str = ""):
    print("Getting posts...")
    await asyncio.sleep(3)
    posts = ["1 Post", "2 Post", "3 Post", "4 Post", "5 Post"]
    return [post for post in posts if search_text.lower() in post.lower()]


class PostsList(ft.Column):
    def __init__(self):

        self.search_text = ft.TextField(
            value="",
            on_change=lambda e: self.posts.refetch(),
        )

        async def request_posts():
            return await get_posts(search_text=self.search_text.value or "")

        self.posts = use_query(
            ("posts", self.search_text.value),
            request_posts,
        )

        super().__init__(controls=[ft.Text("Loading posts...")])

    def before_update(self):
        if self.posts.status == QueryStatus.error:
            self.controls = [ft.Text("Error fetching posts")]

        if self.posts.status == QueryStatus.success and self.posts.data:
            self.controls = [
                self.search_text,
                *(ft.Text(post) for post in self.posts.data),
            ]


async def main(page: ft.Page):
    posts = PostsList()
    page.add(posts)


ft.app(main)
