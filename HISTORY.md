# Release History

## 3.0.0

### Breaking changes

- Renamed abstract methods to match data structure
  Methods are now `message`, `delivery`, `optin`, `postback`, `read` and `account_linking`
- Renamed `subscribe` to `subscribe_app_to_page`

## 2.0.0
- Removed need for verify token when instanciating class
- Removed verify function
- Added callback account_linking webhook
- Support account_link and account_unlink button types
- Message echoes removed, should be handled in messages callback and checking for `"is_echo": "true"`
- Added delete_thread_setting method

## 1.1.0
- Added `BaseMessenger#send_actions` method

## 1.0.0

### Breaking changes

- `Elements#Image` moved to `Attachments#Image`
- `MessengerClient#send_data` renamed to `send`
- `MessengerClient#set_welcome_message removed`
- `BaseMessenger#message_echoes` and `BaseMessenger#message_reads` handlers now required
- Buttons now require a `button_type` parameter


### New features

- Support for audio, video and file attachments
- Support for sender actions
- Support for quick replies
- Support for get started button and persistent menus
- locale, timezone and gender now returned for user
- Support for phone_number button types