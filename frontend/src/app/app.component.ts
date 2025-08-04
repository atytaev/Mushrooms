import { Component, OnInit } from '@angular/core';
import { AuthService } from './auth.service';
import { Router, ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';
import { InspectionsComponent } from './inspections/inspections.component';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  standalone: true,
  imports: [CommonModule,RouterModule]
})
export class AppComponent implements OnInit {
  title = 'hello-angular';
  isLoginPage: boolean = false;

  constructor(public authService: AuthService, private router: Router) {}

  ngOnInit(): void {
    // Проверка на текущий маршрут
    this.router.events.subscribe(() => {
      this.isLoginPage = this.router.url === '/login';  // Проверка, находимся ли на странице входа
    });

    // Подписка на изменение статуса входа
    this.authService.isLoggedIn$.subscribe(isLoggedIn => {
      console.log('isLoggedIn$ changed:', isLoggedIn);
    });
  }

  logout() {
    this.authService.logout().subscribe(() => {
    });
  }
  goToInspections() {
    this.router.navigate(['/inspections']); // или ваш путь к главной странице со списком инспекций
  }
}
