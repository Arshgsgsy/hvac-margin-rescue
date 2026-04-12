from fastapi import APIRouter, UploadFile, File, HTTPException
from config import DATA_DIR, EXPECTED_CSV_FILES

router = APIRouter()


@router.post("/upload")
async def upload_csvs(files: list[UploadFile] = File(...)):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    accepted = []
    for f in files:
        if not f.filename or not f.filename.endswith(".csv"):
            raise HTTPException(400, f"File '{f.filename}' is not a CSV")
        if f.filename not in EXPECTED_CSV_FILES:
            raise HTTPException(
                400,
                f"Unexpected file '{f.filename}'. Expected one of: {EXPECTED_CSV_FILES}",
            )

        dest = DATA_DIR / f.filename
        content = await f.read()
        dest.write_bytes(content)
        accepted.append({"name": f.filename, "size_bytes": len(content)})

    return {"status": "ok", "files": accepted}
