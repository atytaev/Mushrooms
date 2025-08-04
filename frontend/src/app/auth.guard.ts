// auth.guard.ts
import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root',
})
export class AuthGuard implements CanActivate {
  constructor(private authService: AuthService, private router: Router) {}

  canActivate(): boolean {
    const token = localStorage.getItem('access_token');
    console.log('🔑 AuthGuard: Checking access token:', token);

    if (!token) {
      console.log('⛔ No token found! Redirecting to login...');
      this.router.navigate(['/login']);
      return false;
    }

    console.log('✅ Access granted to /bags');
    return true;
  }
}
