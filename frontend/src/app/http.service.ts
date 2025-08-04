// bags.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { AuthService } from './auth.service';
import { catchError, switchMap, tap } from 'rxjs/operators';
import { environment } from '../environments/environment';
import { HttpParams } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})

export class InspectionsService {
  private apiUrl = environment.apiUrl + 'inspections/';

  constructor(private http: HttpClient) {}

  getInspections(): Observable<any[]> {
    return this.http.get<any[]>(`${environment.apiBaseUrl}/api/inspections/`);
  }

  getInspectionById(id: string): Observable<any> {
    return this.http.get<any>(`${environment.apiBaseUrl}/api/inspections/${id}/`);
  }

  getMushroomStorageByInspectionId(id: string): Observable<any> {
   return this.http.get<any>(`${environment.apiBaseUrl}/api/mushroom-storage/?inspection=${id}`);
  }

  getQuantityPhotosByInspectionId(id: string): Observable<any[]> {
    return this.http.get<any[]>(`${environment.apiBaseUrl}/api/quantity-photos/?inspection=${id}`);
  }

  getMarkingPhotosByInspectionId(id: string): Observable<any[]> {
    return this.http.get<any[]>(
      `${environment.apiBaseUrl}/api/marking-photos/?inspection=${id}`
    );
  }

  getQualityPhotosByInspectionId(id: string): Observable<any[]> {
    return this.http.get<any[]>(
      `${environment.apiBaseUrl}/api/quality-photos/?inspection=${id}`
    );
  }

  getPalletPhotosByInspectionId(id: string): Observable<any[]> {
    return this.http.get<any[]>(
      `${environment.apiBaseUrl}/api/pallet-photos/?inspection=${id}`
    );
  }

  getThermometers() {
    return this.http.get<any[]>(`${environment.apiBaseUrl}/api/thermometers/`);
  }

  addThermometer(data: any) {
    return this.http.post<any>(`${environment.apiBaseUrl}/api/thermometers/`, data);
  }

  updateThermometer(id: number, data: any) {
    return this.http.put<any>(`${environment.apiBaseUrl}/api/thermometers/${id}/`, data);
  }

  deleteThermometer(id: number) {
    return this.http.delete(`${environment.apiBaseUrl}/api/thermometers/${id}/`);
  }

  getScales() {
    return this.http.get<any[]>(`${environment.apiBaseUrl}/api/scales/`);
  }

  addScale(data: any) {
    return this.http.post<any>(`${environment.apiBaseUrl}/api/scales/`, data);
  }

  updateScale(id: number, data: any) {
    return this.http.put<any>(`${environment.apiBaseUrl}/api/scales/${id}/`, data);
  }

  deleteScale(id: number) {
    return this.http.delete(`${environment.apiBaseUrl}/api/scales/${id}/`);
  }
}
