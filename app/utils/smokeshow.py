import asyncio
import tempfile
from io import BytesIO
from mimetypes import guess_type
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

import httpx
import streamlit as st

# Smokeshow configuration constants
SMOKESHOW_ROOT_URL = "https://smokeshow.helpmanual.io"
SMOKESHOW_USER_AGENT = "streamlit-smokeshow-uploader"
SMOKESHOW_REQUEST_RETRIES = 5
SMOKESHOW_DEFAULT_TIMEOUT = 50  # seconds
SMOKESHOW_UPLOAD_TIMEOUT = 400  # seconds
SMOKESHOW_MAX_CONCURRENT_UPLOADS = 20


@st.cache_data(show_spinner=False)
def extract_and_upload_coverage_report(artifact_content: bytes) -> Optional[str]:
    """Extract coverage HTML report from artifact and upload to smokeshow."""
    # Create a temporary directory to extract files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        try:
            with ZipFile(BytesIO(artifact_content)) as zip_file:
                # Extract all HTML files
                for file in zip_file.namelist():
                    zip_file.extract(file, temp_path)

                # Upload the directory to smokeshow
                url = asyncio.run(upload_to_smokeshow(temp_path))
                return url
        except Exception as e:
            st.error(f"Error processing coverage report: {e}")
            return None


async def upload_to_smokeshow(directory_path: Path) -> str:
    """Upload a directory to smokeshow and return the URL."""
    auth_key = st.secrets.get("smokeshow_auth_key")
    if not auth_key:
        raise ValueError("Smokeshow auth key not found in secrets")

    transport = httpx.AsyncHTTPTransport(retries=SMOKESHOW_REQUEST_RETRIES)
    async with httpx.AsyncClient(
        timeout=SMOKESHOW_DEFAULT_TIMEOUT,
        transport=transport,
    ) as client:
        try:
            r = await client.post(
                SMOKESHOW_ROOT_URL + "/create/",
                headers={"Authorisation": auth_key, "User-Agent": SMOKESHOW_USER_AGENT},
            )
        except httpx.HTTPError as err:
            raise ValueError(f"Error creating ephemeral site {err}")

        if r.status_code != 200:
            raise ValueError(
                f"Error creating ephemeral site {r.status_code}, response:\n{r.text}"
            )

        obj = r.json()
        secret_key: str = obj["secret_key"]
        upload_root: str = obj["url"]

        # Create a list of files to upload
        files_to_upload = []
        for p in directory_path.glob("**/*"):
            if p.is_file():
                files_to_upload.append((p, p.relative_to(directory_path)))

        # Create a semaphore to limit concurrent uploads to 60
        semaphore = asyncio.Semaphore(SMOKESHOW_MAX_CONCURRENT_UPLOADS)

        # Define a wrapper function that uses the semaphore
        async def upload_with_semaphore(file_path, rel_path):
            async with semaphore:
                await _upload_file(
                    client,
                    secret_key,
                    upload_root,
                    file_path,
                    rel_path,
                    SMOKESHOW_UPLOAD_TIMEOUT,
                )

        # Create and schedule all tasks
        tasks = [
            asyncio.create_task(upload_with_semaphore(file_path, rel_path))
            for file_path, rel_path in files_to_upload
        ]

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            st.error(f"Error uploading files: {e}")
            raise

        return upload_root


async def _upload_file(
    client: httpx.AsyncClient,
    secret_key: str,
    upload_root: str,
    file_path: Path,
    rel_path: Path,
    timeout: int,
) -> None:
    """Upload a single file to smokeshow."""

    url_path = str(rel_path)

    headers = {"Authorisation": secret_key, "User-Agent": SMOKESHOW_USER_AGENT}

    ct = guess_type(url_path)[0]
    if ct:
        headers["Content-Type"] = ct

    try:
        response = await client.post(
            upload_root + url_path,
            content=file_path.read_bytes(),
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
    except Exception as ex:
        st.error(f"Error uploading {url_path}: {ex}")
        raise
