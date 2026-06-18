from __future__ import annotations

import os
from dataclasses import dataclass

CHATGPT_LOGIN_URL = "https://chatgpt.com/"
CHATGPT_LOGOUT_URL = "https://chatgpt.com/auth/logout"


@dataclass(frozen=True)
class ChatGPTSubscriptionStatus:
    state: str
    label: str
    detail: str
    action_label: str
    action_url: str
    active: bool


def current_chatgpt_subscription_status() -> ChatGPTSubscriptionStatus:
    active = os.getenv("CHATGPT_SUBSCRIPTION_ACTIVE", "").lower() in {"1", "true", "yes"}
    if active:
        return ChatGPTSubscriptionStatus(
            state="external-active",
            label="external subscription declared",
            detail=(
                "A local configuration flag declares the ChatGPT account active. The app still "
                "keeps credentials outside Python and consumes visual categorizer result artifacts."
            ),
            action_label="Open ChatGPT logout",
            action_url=CHATGPT_LOGOUT_URL,
            active=True,
        )
    return ChatGPTSubscriptionStatus(
        state="external-unverified",
        label="external login unverified",
        detail=(
            "Open ChatGPT in the browser for visual categorizer review. This Python app cannot "
            "inspect ChatGPT browser-session or subscription state, and does not store credentials."
        ),
        action_label="Open ChatGPT login",
        action_url=CHATGPT_LOGIN_URL,
        active=False,
    )
