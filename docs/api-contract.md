# GymGate API Contract

> **Base URL:** `/api/v1`  
> **Format:** JSON  
> **Auth:** JWT (Admin panel) | API Key (Gate device)

---

## Auth — Login

### `POST /auth/register`
Creates a new gym and admin account.

**Body:**
```json
{
  "gym_name": "PowerGym",
  "gym_address": "Kadikoy, Istanbul",
  "gym_phone": "+905551234567",
  "gym_email": "info@powergym.com",
  "gym_max_capacity": 80,
  "admin_email": "admin@powergym.com",
  "admin_password": "SecurePass123!",
  "admin_full_name": "Ahmet Yilmaz"
}
```

**Response `201`:**
```json
{
  "gym_id": "uuid",
  "admin_id": "uuid",
  "message": "Gym and admin created"
}
```

---

### `POST /auth/login`
Admin login, returns JWT token.

**Body:**
```json
{
  "email": "admin@powergym.com",
  "password": "SecurePass123!"
}
```

**Response `200`:**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "gym_id": "uuid"
}
```

---

## Gym — Gym Info

> Auth: JWT

### `GET /gyms/me`
Returns the admin's own gym info.

### `PUT /gyms/me`
Updates gym info (name, capacity, etc.)

---

## Members — Member Management

> Auth: JWT — Only shows members from the admin's own gym (tenant isolation)

### `GET /members`
Lists members. Supports pagination and search.

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | int | Page number (default: 1) |
| `per_page` | int | Items per page (default: 20) |
| `search` | string | Search by name/email |
| `is_active` | bool | Active/inactive filter |
| `is_flagged` | bool | Flagged member filter |

### `POST /members`
Adds a new member.

**Body:**
```json
{
  "first_name": "Mehmet",
  "last_name": "Demir",
  "email": "mehmet@email.com",
  "phone": "+905559876543",
  "date_of_birth": "1995-03-20",
  "emergency_contact": "+905551112233"
}
```

### `GET /members/{member_id}`
Single member details.

### `PUT /members/{member_id}`
Updates member info.

### `DELETE /members/{member_id}`
Deactivates the member (soft delete, sets `is_active = false`).

### `POST /members/{member_id}/flag`
Flags a member (with a reason).

### `DELETE /members/{member_id}/flag`
Removes the flag.

---

## Plans — Membership Plans

> Auth: JWT

### `GET /plans`
Lists all plans.

### `POST /plans`
Creates a new plan.

**Body:**
```json
{
  "name": "Monthly Membership",
  "description": "30 days unlimited access",
  "duration_days": 30,
  "price": 500.00
}
```

### `PUT /plans/{plan_id}`
Updates a plan.

### `DELETE /plans/{plan_id}`
Deactivates a plan.

---

## Subscriptions

> Auth: JWT

### `POST /members/{member_id}/subscriptions`
Assigns a plan to a member.

**Body:**
```json
{
  "plan_id": "uuid",
  "start_date": "2026-05-15"
}
```

### `GET /members/{member_id}/subscriptions`
Member's subscription history.

### `PUT /subscriptions/{sub_id}/freeze`
Freezes a subscription.

### `PUT /subscriptions/{sub_id}/unfreeze`
Unfreezes a subscription.

### `PUT /subscriptions/{sub_id}/cancel`
Cancels a subscription.

---

## Credentials — QR Code & NFC

> Auth: JWT

### `POST /members/{member_id}/credentials/qr`
Generates an encrypted QR code for the member. Returns the QR image as base64.

### `POST /members/{member_id}/credentials/nfc`
Assigns an NFC tag to a member.

**Body:**
```json
{
  "nfc_tag_uid": "04:A2:3B:C1:D4:56:78"
}
```

### `GET /members/{member_id}/credentials`
Lists member's credentials.

### `DELETE /credentials/{credential_id}`
Revokes a credential.

---

## Gate Devices

> Auth: JWT

### `GET /devices`
Lists gate devices.

### `POST /devices`
Registers a new device. Returns an API key (shown only once!).

### `DELETE /devices/{device_id}`
Deactivates a device.

---

## Verify — Verification Engine ⚡

> Auth: API Key (`X-API-Key` header)  
> Rate Limit: 60 requests/minute  
> Target: < 200ms

This is the most critical endpoint in the project. The gate device sends a request to this endpoint, and the system either grants or denies entry.

### `POST /verify`

**Body:**
```json
{
  "credential_type": "qr",
  "credential_value": "encrypted_qr_data_here",
  "action": "entry"
}
```

**Access granted:**
```json
{
  "access": "granted",
  "member": {
    "first_name": "Mehmet",
    "last_name": "Demir"
  },
  "subscription_status": "active",
  "gym_occupancy": {
    "current": 24,
    "max": 80
  }
}
```

**Access denied:**
```json
{
  "access": "denied",
  "reason": "expired",
  "message": "Membership has expired"
}
```

**Flagged member (personal info hidden):**
```json
{
  "access": "denied",
  "reason": "flagged",
  "message": "Member is flagged, contact management"
}
```

**Denial reasons:**
| Reason | Description |
|--------|-------------|
| `expired` | Membership expired |
| `frozen` | Membership frozen |
| `flagged` | Member is flagged |
| `invalid` | Invalid QR/NFC |
| `inactive` | Member is inactive |
| `capacity_full` | Gym is full |
| `no_subscription` | No active subscription |

---

## Access Logs

> Auth: JWT

### `GET /access-logs`
Returns entry/exit records. Supports date, member, and status filters.

---

## Occupancy

> Auth: JWT or API Key

### `GET /occupancy`
Returns real-time occupancy from Redis.

```json
{
  "current_occupancy": 24,
  "max_capacity": 80,
  "utilization_percentage": 30.0
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| `400` | Bad request |
| `401` | Not authenticated |
| `403` | Unauthorized (trying to access another gym's data) |
| `404` | Not found |
| `422` | Invalid data format |
| `429` | Rate limit exceeded |
| `500` | Server error |
