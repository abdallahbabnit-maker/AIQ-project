import hashlib
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.asset import Asset
from app.core.security import require_user

router = APIRouter(prefix="/studio", tags=["studio"])

PALETTES = [("#7C3AED", "#06B6D4"), ("#F43F5E", "#FB923C"),
            ("#10B981", "#3B82F6"), ("#8B5CF6", "#EC4899"),
            ("#0EA5E9", "#6366F1")]


class GenBody(BaseModel):
    prompt: str
    kind: str = "image"


@router.get("/assets")
async def list_assets(session: AsyncSession = Depends(get_session),
                      user: dict = Depends(require_user)):
    rows = (await session.execute(
        select(Asset).order_by(Asset.created_at.desc())
    )).scalars().all()
    return [{"id": a.id, "kind": a.kind, "prompt": a.prompt,
             "status": a.status, "url": f"/studio/render/{a.id}",
             "created_at": a.created_at.isoformat()} for a in rows]


@router.post("/generate")
async def generate(body: GenBody, session: AsyncSession = Depends(get_session),
                   user: dict = Depends(require_user)):
    a = Asset(kind=body.kind, prompt=body.prompt, status="ready",
              meta={"by": user["sub"]})
    session.add(a)
    await session.commit()
    return {"id": a.id, "url": f"/studio/render/{a.id}"}


@router.post("/assets/{asset_id}/regenerate")
async def regenerate(asset_id: str, session: AsyncSession = Depends(get_session),
                     user: dict = Depends(require_user)):
    a = await session.get(Asset, asset_id)
    if not a:
        raise HTTPException(404, "asset_not_found")
    a.meta = {**a.meta, "regen": a.meta.get("regen", 0) + 1,
              "seed": str(uuid.uuid4())[:8]}
    await session.commit()
    return {"ok": True, "url": f"/studio/render/{a.id}"}


@router.patch("/assets/{asset_id}")
async def edit(asset_id: str, body: dict,
               session: AsyncSession = Depends(get_session),
               user: dict = Depends(require_user)):
    a = await session.get(Asset, asset_id)
    if not a:
        raise HTTPException(404, "asset_not_found")
    if "prompt" in body:
        a.prompt = body["prompt"]
    if "title" in body:
        a.meta = {**a.meta, "title": body["title"]}
    await session.commit()
    return {"ok": True}


@router.get("/render/{asset_id}")
async def render(asset_id: str, session: AsyncSession = Depends(get_session)):
    a = await session.get(Asset, asset_id)
    if not a:
        raise HTTPException(404, "asset_not_found")
    seed = hashlib.md5((a.id + a.meta.get("seed", "")).encode()).hexdigest()
    p1, p2 = PALETTES[int(seed[:2], 16) % len(PALETTES)]
    label = a.prompt[:28]
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='640' height='400'>
<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>
<stop offset='0' stop-color='{p1}'/><stop offset='1' stop-color='{p2}'/>
</linearGradient></defs>
<rect width='640' height='400' fill='url(#g)'/>
<circle cx='{100+int(seed[2:4],16)}' cy='120' r='90' fill='white' opacity='.12'/>
<circle cx='{420-int(seed[4:6],16)}' cy='300' r='130' fill='black' opacity='.18'/>
<text x='32' y='360' font-family='sans-serif' font-size='22' fill='white' opacity='.95'>{label}</text>
</svg>"""
    return Response(svg, media_type="image/svg+xml")
