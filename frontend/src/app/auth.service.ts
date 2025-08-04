import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { Router } from '@angular/router';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = environment.apiUrl;
  private refreshTokenUrl = environment.refreshTokenUrl;
  private isLoggedInSubject = new BehaviorSubject<boolean>(this.hasToken());
  public isLoggedIn$ = this.isLoggedInSubject.asObservable();
  private refreshTokenInProgress = false;
  private refreshTokenSubject: BehaviorSubject<any> = new BehaviorSubject<any>(null);

  constructor(private http: HttpClient, private router: Router) {}

  // Проверка, если пользователь авторизован
  isAuthenticated(): boolean {
    return this.hasToken();
  }

  // Сохранение токена
  setToken(token: string): void {
    localStorage.setItem('access_token', token);
    this.setLoginStatus(true);
  }

  // Проверка наличия токена
  hasToken(): boolean {
    return localStorage.getItem('access_token') !== null;
  }

  // Логин пользователя
  login(username: string, password: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}token/`, { username, password }).pipe(
      tap(data => {
        localStorage.setItem('username', username);
        this.setToken(data.access); // Сохраняем токен
        localStorage.setItem('refresh_token', data.refresh);
      }),
    );
  }

  // Логика выхода
  logout(): Observable<void> {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('username');
    this.setLoginStatus(false);
    this.router.navigate(['login']);
    return of();  // Возвращаем Observable, который ничего не эмитирует
  }

  // Обновление токена
  refreshToken(): Observable<any> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      return this.logout();  // Теперь logout() возвращает Observable
    }

    return this.http.post<any>(`${this.refreshTokenUrl}`, { refresh: refreshToken }).pipe(
      tap((response) => {
        this.setToken(response.access);  // Обновляем access token
      }),
      catchError(error => {
        this.logout();  // В случае ошибки - выходим
        throw error;
      })
    );
  }

  // Проверка, если пользователь авторизован
  setLoginStatus(status: boolean): void {
    console.log('Login status:', status);
    this.isLoggedInSubject.next(status);  // Обновляем состояние авторизации
  }

  getUserName(): string {
    const username = localStorage.getItem('username');
    return username ? username : 'Гость'; // Возвращаем имя или 'Гость' если имя не найдено
  }
}
