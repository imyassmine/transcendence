# transcendence

## Notification event contract

Backend event producers share `NotificationEvent` and `NotificationType` from
`schemas`. The notification handler currently supports `account.created`.

For `account.created`, build a `NotificationEvent` with
`type="account.created"`, the account owner's `user_id`, a timezone-aware
`created_at`, and `meta_data={"platform_name": "GitHub"}`. Generate an
`event_id` for each new action and reuse it when retrying that action.

Call `create_notification_event_handler(event, session)` in the caller's
transaction. The handler writes to `notifications` and uses its unique
`event_id` to deduplicate retries.
