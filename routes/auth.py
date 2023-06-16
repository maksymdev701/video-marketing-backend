from fastapi import APIRouter, HTTPException, Depends, status, Request, Body

router = APIRouter(prefix="/api/auth", tags=["auth"])
