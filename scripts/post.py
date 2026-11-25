"""queue.json 에서 올릴 차례인 게시물 1개를 인스타그램에 업로드합니다.

Instagram API (Instagram 로그인 방식, graph.instagram.com) 사용.
필요한 환경변수:
  IG_USER_ID       인스타그램 비즈니스/크리에이터 계정 ID
  IG_ACCESS_TOKEN  장기 액세스 토큰
  IMAGE_BASE_URL   (선택) images/ 폴더 파일을 공개 URL로 바꿀 때 쓰는 주소.
                   GitHub Actions에서는 자동으로 raw.githubusercontent.com 주소를 만듭니다.
  DRY_RUN=1        (선택) 실제 업로드 없이 무엇을 올릴지만 출력
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = "https://graph.instagram.com/v21.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE = os.path.join(ROOT, "queue.json")


def api(method, path, **params):
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        url, data = f"{url}?{data.decode()}", None
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"API 오류 {e.code}: {e.read().decode()}")


def image_url(item):
    img = item["image"]
    if img.startswith("http://") or img.startswith("https://"):
        return img
    base = os.environ.get("IMAGE_BASE_URL")
    if not base:
        repo, sha = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_SHA")
        if not (repo and sha):
            sys.exit("이미지 공개 URL을 만들 수 없습니다. IMAGE_BASE_URL을 설정하거나 image에 전체 URL을 쓰세요.")
        base = f"https://raw.githubusercontent.com/{repo}/{sha}"
    return f"{base.rstrip('/')}/{img.lstrip('/')}"


def is_due(item, now):
    if item.get("posted_at"):
        return False
    at = item.get("publish_at")
    if not at:
        return True
    return datetime.fromisoformat(at).astimezone(timezone.utc) <= now


def main():
    with open(QUEUE, encoding="utf-8") as f:
        queue = json.load(f)

    now = datetime.now(timezone.utc)
    item = next((p for p in queue if is_due(p, now)), None)
    if item is None:
        print("올릴 게시물이 없습니다.")
        return

    url = image_url(item)
    caption = item.get("caption", "")
    print(f"업로드 대상: {url}\n캡션: {caption[:80]}")

    if os.environ.get("DRY_RUN") == "1":
        print("DRY_RUN: 실제 업로드는 건너뜁니다.")
        return

    user_id = os.environ["IG_USER_ID"]
    token = os.environ["IG_ACCESS_TOKEN"]

    # 1) 미디어 컨테이너 생성
    container = api("POST", f"{user_id}/media", image_url=url, caption=caption, access_token=token)["id"]

    # 2) 처리 완료까지 대기
    for _ in range(30):
        status = api("GET", container, fields="status_code", access_token=token).get("status_code")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            sys.exit(f"미디어 처리 실패: {status}")
        time.sleep(5)
    else:
        sys.exit("미디어 처리 시간 초과")

    # 3) 게시
    media_id = api("POST", f"{user_id}/media_publish", creation_id=container, access_token=token)["id"]
    print(f"게시 완료: media_id={media_id}")

    item["posted_at"] = now.isoformat(timespec="seconds")
    item["media_id"] = media_id
    with open(QUEUE, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
