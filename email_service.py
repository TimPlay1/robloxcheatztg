"""
Email Service для отправки верификационных кодов
Поддерживает: Resend API, SMTP (Gmail и др.)
"""

import aiohttp
import asyncio
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import Optional, Dict
from datetime import datetime


class EmailService:
    """Сервис отправки email с поддержкой нескольких провайдеров"""
    
    def __init__(self):
        # Resend API (рекомендуется)
        self.resend_api_key = os.getenv("RESEND_API_KEY", "")
        self.resend_from_email = os.getenv("RESEND_FROM_EMAIL", "noreply@robloxcheatz.com")
        
        # SMTP настройки (альтернатива)
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from_email = os.getenv("SMTP_FROM_EMAIL", "")
        
        # Определяем провайдер
        if self.resend_api_key:
            self.provider = "resend"
            print("[OK] Email service: Resend API")
        elif self.smtp_user and self.smtp_password:
            self.provider = "smtp"
            print(f"[OK] Email service: SMTP ({self.smtp_host})")
        else:
            self.provider = "none"
            print("[!] Email service: Not configured (codes will be shown in Discord)")
    
    def _get_verification_html(self, code: str, username: str) -> str:
        """Генерация HTML письма с кодом верификации"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0a0a0f;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 100%; max-width: 600px; border-collapse: collapse; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 16px; overflow: hidden; box-shadow: 0 20px 60px rgba(138, 43, 226, 0.3);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 50%, #c084fc 100%);">
                            <img src="https://robloxcheatztg.vercel.app/logo.jpg" alt="RobloxCheatz" style="width: 80px; height: 80px; border-radius: 50%; border: 4px solid rgba(255,255,255,0.3); margin-bottom: 16px;">
                            <h1 style="color: #ffffff; font-size: 28px; margin: 0; font-weight: 700; text-shadow: 0 2px 10px rgba(0,0,0,0.3);">RobloxCheatz</h1>
                            <p style="color: rgba(255,255,255,0.9); font-size: 14px; margin: 8px 0 0; letter-spacing: 1px;">VERIFICATION CODE</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <p style="color: #e2e8f0; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
                                Hey <strong style="color: #a855f7;">{username}</strong>! 👋
                            </p>
                            <p style="color: #94a3b8; font-size: 15px; line-height: 1.6; margin: 0 0 32px;">
                                You requested a verification code to link your Discord account. Use the code below to complete your verification:
                            </p>
                            
                            <!-- Code Box - Clickable to copy -->
                            <div style="background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); border: 2px solid #8b5cf6; border-radius: 12px; padding: 24px; text-align: center; margin: 0 0 16px;">
                                <p style="color: #a855f7; font-size: 12px; letter-spacing: 2px; margin: 0 0 12px; text-transform: uppercase;">Your Verification Code</p>
                                <p style="color: #ffffff; font-size: 42px; font-weight: 700; letter-spacing: 8px; margin: 0; font-family: 'Courier New', monospace; user-select: all;">{code}</p>
                            </div>
                            
                            <!-- Copy hint -->
                            <p style="color: #64748b; font-size: 12px; text-align: center; margin: 0 0 24px;">
                                📋 Select the code above and copy it (Ctrl+C / Cmd+C)
                            </p>
                            
                            <p style="color: #64748b; font-size: 14px; line-height: 1.6; margin: 0 0 16px;">
                                ⏱️ This code expires in <strong style="color: #f59e0b;">30 minutes</strong>.
                            </p>
                            <p style="color: #64748b; font-size: 14px; line-height: 1.6; margin: 0;">
                                🔒 If you didn't request this code, you can safely ignore this email.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 40px; background: rgba(0,0,0,0.3); border-top: 1px solid rgba(139, 92, 246, 0.3);">
                            <p style="color: #64748b; font-size: 12px; text-align: center; margin: 0 0 8px;">
                                © {datetime.now().year} RobloxCheatz. All rights reserved.
                            </p>
                            <p style="color: #475569; font-size: 11px; text-align: center; margin: 0;">
                                🛡️ This is an automated message. Please do not reply to this email.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
    def _get_verification_text(self, code: str, username: str) -> str:
        """Текстовая версия письма"""
        return f"""
RobloxCheatz - Verification Code

Hey {username}!

You requested a verification code to link your Discord account.

Your verification code: {code}

This code expires in 30 minutes.

If you didn't request this code, you can safely ignore this email.

© {datetime.now().year} RobloxCheatz
"""
    
    async def send_verification_code(self, to_email: str, code: str, username: str = "User") -> Dict:
        """
        Отправить код верификации на email
        
        Returns:
            {"success": True/False, "error": "message if failed", "provider": "resend/smtp/none"}
        """
        if self.provider == "none":
            return {
                "success": False,
                "error": "Email service not configured",
                "provider": "none"
            }
        
        if self.provider == "resend":
            return await self._send_via_resend(to_email, code, username)
        elif self.provider == "smtp":
            return await self._send_via_smtp(to_email, code, username)
        
        return {"success": False, "error": "Unknown provider", "provider": self.provider}
    
    async def _send_via_resend(self, to_email: str, code: str, username: str) -> Dict:
        """Отправка через Resend API"""
        url = "https://api.resend.com/emails"
        
        headers = {
            "Authorization": f"Bearer {self.resend_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "from": self.resend_from_email,
            "to": [to_email],
            "subject": f"🔐 Your RobloxCheatz Verification Code: {code}",
            "html": self._get_verification_html(code, username),
            "text": self._get_verification_text(code, username)
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=30) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        print(f"[EMAIL] Sent verification code to {to_email[:3]}***@*** via Resend")
                        return {"success": True, "provider": "resend", "id": result.get("id")}
                    else:
                        error_msg = result.get("message", result.get("error", "Unknown error"))
                        print(f"[EMAIL] Resend error: {error_msg}")
                        return {"success": False, "error": error_msg, "provider": "resend"}
        
        except asyncio.TimeoutError:
            return {"success": False, "error": "Request timeout", "provider": "resend"}
        except Exception as e:
            return {"success": False, "error": str(e), "provider": "resend"}
    
    async def _send_via_smtp(self, to_email: str, code: str, username: str) -> Dict:
        """Отправка через SMTP"""
        try:
            # Создаем сообщение
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🔐 Your RobloxCheatz Verification Code: {code}"
            msg["From"] = self.smtp_from_email or self.smtp_user
            msg["To"] = to_email
            
            # Добавляем текстовую и HTML версии
            text_part = MIMEText(self._get_verification_text(code, username), "plain", "utf-8")
            html_part = MIMEText(self._get_verification_html(code, username), "html", "utf-8")
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Отправляем в отдельном потоке чтобы не блокировать
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._smtp_send, msg, to_email)
            
            print(f"[EMAIL] Sent verification code to {to_email[:3]}***@*** via SMTP")
            return {"success": True, "provider": "smtp"}
        
        except Exception as e:
            print(f"[EMAIL] SMTP error: {e}")
            return {"success": False, "error": str(e), "provider": "smtp"}
    
    def _smtp_send(self, msg: MIMEMultipart, to_email: str):
        """Синхронная отправка через SMTP"""
        context = ssl.create_default_context()
        
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls(context=context)
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(
                self.smtp_from_email or self.smtp_user,
                to_email,
                msg.as_string()
            )
    
    def is_configured(self) -> bool:
        """Проверка настроен ли email сервис"""
        return self.provider != "none"


# Глобальный экземпляр
email_service = EmailService()
