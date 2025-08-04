// app.config.ts
import { ApplicationConfig } from '@angular/core';
import { provideRouter, Routes } from '@angular/router';
import { LoginComponent } from './login/login.component';
import { AuthGuard } from './auth.guard';
import { InspectionsComponent } from './inspections/inspections.component';
import { InspectionDetailComponent } from './inspection-detail/inspection-detail.component';

import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { provideHttpClient } from '@angular/common/http';

const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },  // Redirect to login by default
  { path: 'login', component: LoginComponent },
  { path: 'inspections', component: InspectionsComponent, canActivate: [AuthGuard] }, // Protecting the bags route
  { path: 'inspections/:id', component: InspectionDetailComponent, canActivate: [AuthGuard] },
];

console.log('🛤️ Routes initialized:', routes);

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideHttpClient(), // Без этого Angular не сможет делать HTTP-запросы!
  ]
};
