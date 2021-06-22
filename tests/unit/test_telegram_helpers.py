from unittest.mock import patch
from src import telegram_helpers


@patch("src.telegram_helpers.requests")
@patch("src.telegram_helpers.BOT_TOKEN", "123")
def test_given_message_when_send_text_then_request_made(requests_mock):

    chat_id = 123
    message = "hello!"
    requests_mock.get.return_value.status_code = 200

    result = telegram_helpers.send_text(chat_id, message)

    requests_mock.get.assert_called_once_with(f'https://api.telegram.org/bot123/sendMessage?chat_id='
                                              f'{chat_id}&parse_mode=Markdown&text={message}', timeout=5)

    assert result == requests_mock.get.return_value.json.return_value
    requests_mock.get.return_value.raise_for_status.assert_not_called()


@patch("src.telegram_helpers.requests")
@patch("src.telegram_helpers.BOT_TOKEN", "123")
def test_given_400_when_send_text_then_no_raise(requests_mock):

    chat_id = 123
    message = "hello!"
    requests_mock.get.return_value.status_code = 400

    result = telegram_helpers.send_text(chat_id, message)

    requests_mock.get.assert_called_once_with(f'https://api.telegram.org/bot123/sendMessage?chat_id='
                                              f'{chat_id}&parse_mode=Markdown&text={message}', timeout=5)

    assert result == requests_mock.get.return_value.json.return_value
    requests_mock.get.return_value.raise_for_status.assert_not_called()


@patch("src.telegram_helpers.requests")
@patch("src.telegram_helpers.BOT_TOKEN", "123")
def test_given_403_when_send_text_then_no_raise(requests_mock):

    chat_id = 123
    message = "hello!"
    requests_mock.get.return_value.status_code = 403

    result = telegram_helpers.send_text(chat_id, message)

    requests_mock.get.assert_called_once_with(f'https://api.telegram.org/bot123/sendMessage?chat_id='
                                              f'{chat_id}&parse_mode=Markdown&text={message}', timeout=5)

    assert result == requests_mock.get.return_value.json.return_value
    requests_mock.get.return_value.raise_for_status.assert_not_called()


@patch("src.telegram_helpers.requests")
@patch("src.telegram_helpers.BOT_TOKEN", "123")
def test_given_401_when_send_text_then_riase_called(requests_mock):

    chat_id = 123
    message = "hello!"
    requests_mock.get.return_value.status_code = 401

    result = telegram_helpers.send_text(chat_id, message)

    requests_mock.get.assert_called_once_with(f'https://api.telegram.org/bot123/sendMessage?chat_id='
                                              f'{chat_id}&parse_mode=Markdown&text={message}', timeout=5)

    assert result == requests_mock.get.return_value.json.return_value
    requests_mock.get.return_value.raise_for_status.assert_called_once_with()

