"""Windows DPAPI user-scoped storage for locally configured API secrets."""

from __future__ import annotations

import base64
import ctypes
import os
from ctypes import wintypes


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def _windows_api():
    if os.name != "nt":
        raise RuntimeError("保存 API Key 需要 Windows 用户加密存储")
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(_DataBlob), wintypes.LPCWSTR, ctypes.POINTER(_DataBlob),
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_DataBlob),
    ]
    crypt32.CryptProtectData.restype = wintypes.BOOL
    crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(_DataBlob), ctypes.c_void_p, ctypes.POINTER(_DataBlob),
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_DataBlob),
    ]
    crypt32.CryptUnprotectData.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    return crypt32, kernel32


def _input_blob(raw: bytes):
    buffer = ctypes.create_string_buffer(raw)
    blob = _DataBlob(len(raw), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    return blob, buffer


def protect_secret(secret: str) -> str:
    crypt32, kernel32 = _windows_api()
    source, buffer = _input_blob(secret.encode("utf-8"))
    result = _DataBlob()
    if not crypt32.CryptProtectData(ctypes.byref(source), "BookWorldSimulator", None, None, None, 0x1, ctypes.byref(result)):
        raise RuntimeError(f"无法加密 API Key（Windows 错误 {ctypes.get_last_error()}）")
    try:
        return "dpapi:" + base64.b64encode(ctypes.string_at(result.pbData, result.cbData)).decode("ascii")
    finally:
        kernel32.LocalFree(result.pbData)


def unprotect_secret(value: str) -> str:
    if not value.startswith("dpapi:"):
        raise RuntimeError("API Key 存储格式不受支持")
    crypt32, kernel32 = _windows_api()
    try:
        raw = base64.b64decode(value[6:], validate=True)
    except (ValueError, base64.binascii.Error):
        raise RuntimeError("API Key 存储内容无效") from None
    source, buffer = _input_blob(raw)
    result = _DataBlob()
    if not crypt32.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 0x1, ctypes.byref(result)):
        raise RuntimeError("无法解锁 API Key；请使用保存它的 Windows 用户账户")
    try:
        return ctypes.string_at(result.pbData, result.cbData).decode("utf-8")
    finally:
        kernel32.LocalFree(result.pbData)
