// login.component.ts
import { AuthService } from '../auth.service';
import { Router } from '@angular/router';
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';


@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css'],
  standalone: true,
  imports: [CommonModule, FormsModule],  // Добавляем
})
export class LoginComponent {
  username = '';
  password = '';
  errorMessage = '';

  constructor(private authService: AuthService, private router: Router) {}

  login() {
    this.authService.login(this.username, this.password).subscribe(
      (data: any) => {
        console.log('Access Token:', data.access);
        console.log('Refresh Token:', data.refresh);

        this.authService.setToken(data.access);
        this.router.navigate(['/inspections']);  // Перенаправление после входа
      },
      () => {
        this.errorMessage = 'Ошибка входа. Проверьте логин или пароль.';
      }
    );
  }
}
