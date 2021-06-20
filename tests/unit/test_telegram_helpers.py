from unittest.mock import patch
from src import telegram_helpers


@patch("src.telegram_helpers.requests")
@patch("src.telegram_helpers.BOT_TOKEN", "123")
def test_given_message_when_send_text_then_request_made(requests_mock):

    chat_id = 123
    message = "hello!"
    result = telegram_helpers.send_text(chat_id, message)

    requests_mock.get.assert_called_once_with(f'https://api.telegram.org/bot123/sendMessage?chat_id='
                                              f'{chat_id}&parse_mode=Markdown&text={message}', timeout=5)

    assert result == requests_mock.get.return_value.json.return_value
