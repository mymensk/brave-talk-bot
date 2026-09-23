import pytest

from brave_talk_bot.llm import Completion, RefusalKind, classify_refusal


def _completion(text: str, finish_reason: str = "stop") -> Completion:
    return Completion(text=text, finish_reason=finish_reason, prompt_tokens=0, completion_tokens=0)


def test_blacklist_is_hard_refusal() -> None:
    assert classify_refusal(_completion("", "blacklist")) is RefusalKind.HARD


@pytest.mark.parametrize(
    "text",
    [
        "Что-то в вашем вопросе меня смущает. Может, поговорим на другую тему?",
        "Не люблю менять тему разговора, но вот сейчас тот самый случай.",
        "Давайте поговорим о чём-нибудь другом.",
    ],
)
def test_canned_deflection_is_soft_refusal(text: str) -> None:
    assert classify_refusal(_completion(text)) is RefusalKind.SOFT


def test_short_generic_refusal_is_soft() -> None:
    assert classify_refusal(_completion("Извините, я не могу помочь с этим.")) is RefusalKind.SOFT


def test_long_answer_with_generic_phrase_is_not_refusal() -> None:
    text = (
        "1. Сдержанный: «Прости, я был неправ и не могу помочь себе не думать об этом». "
        + "Эффект: спокойное признание ошибки без оправданий. " * 10
    )
    assert classify_refusal(_completion(text)) is RefusalKind.NONE


def test_regular_answer_is_not_refusal() -> None:
    text = "1. Смелый: «Твоя подборка музыки выдаёт в тебе опасного человека». Эффект: игра."
    assert classify_refusal(_completion(text)) is RefusalKind.NONE
