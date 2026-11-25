# 인스타그램 예약 업로드 (GitHub Actions)

`queue.json`에 게시물을 적어두면, GitHub Actions가 **매일 오전 9시(KST)**에 올릴 차례인 게시물을 **1개** 업로드합니다.
업로드가 끝나면 `posted_at`이 기록되고 자동으로 커밋돼서, 같은 게시물이 두 번 올라가지 않아요.

## 1. 준비물

- 인스타그램 **비즈니스** 또는 **크리에이터** 계정 (앱 설정 → 계정 유형 전환)
- [Meta for Developers](https://developers.facebook.com/) 앱
  1. 앱 만들기 → 사용 사례에서 **"Instagram에서 메시지 및 콘텐츠 관리"** 선택
  2. **Instagram API (Instagram 로그인)** → 권한 `instagram_business_basic`, `instagram_business_content_publish`
  3. "액세스 토큰 생성"에서 내 인스타 계정을 연결하면 **계정 ID**와 **토큰**이 나옵니다

## 2. GitHub 저장소 설정

**Settings → Secrets and variables → Actions → New repository secret**

| 이름 | 값 |
|---|---|
| `IG_USER_ID` | 인스타 계정 ID (숫자) |
| `IG_ACCESS_TOKEN` | 장기 액세스 토큰 |

> ⚠️ 이미지 URL: 인스타 API는 **공개 URL**의 이미지만 가져올 수 있어요.
> - **공개 저장소**: 설정할 것 없음. `images/`의 파일을 자동으로 `raw.githubusercontent.com` 주소로 바꿔요.
> - **비공개 저장소**: `queue.json`의 `image`에 전체 URL(`https://...jpg`)을 쓰거나, Variables에 `IMAGE_BASE_URL`을 설정하세요.

## 3. 게시물 추가

1. `images/` 폴더에 JPG 이미지 업로드 (권장 1080×1080 또는 1080×1350, 8MB 이하)
2. `queue.json`에 항목 추가:

```json
{
  "image": "images/0101.jpg",
  "caption": "캡션 내용\n\n#해시태그",
  "publish_at": "2026-12-01T09:00:00+09:00"
}
```

- `publish_at`을 생략하면 다음 실행 때 바로 올라가요.
- 한 번 실행에 1개씩, 위에서부터 순서대로 올립니다.

## 4. 테스트

**Actions → Instagram 예약 업로드 → Run workflow**에서 `dry_run`을 `1`로 실행하면, 실제로 올리지 않고 무엇이 올라갈지만 보여줘요.

## 업로드 시간 바꾸기

`.github/workflows/post.yml`의 `cron`을 수정하세요 (UTC 기준, 한국시간 −9시간).

| 원하는 시간 (KST) | cron |
|---|---|
| 매일 09:00 | `0 0 * * *` |
| 매일 12:00, 19:00 | `0 3,10 * * *` |
| 평일 18:00 | `0 9 * * 1-5` |

## 주의

- 장기 토큰은 **60일** 뒤에 만료돼요. 만료 전에 새로 발급해서 Secret을 바꿔주세요.
- API로는 하루 최대 **50개**까지만 게시할 수 있어요.
- GitHub 예약 실행은 몇 분~수십 분 늦게 시작될 수 있어요.
