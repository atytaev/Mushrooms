import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { InspectionsService } from '../http.service';
import { CommonModule } from '@angular/common';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { TemplateRef } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';


@Component({
  selector: 'app-inspection-detail',
  standalone: true,
  templateUrl: './inspection-detail.component.html',
  styleUrls: ['./inspection-detail.component.css'],
  imports: [
    CommonModule,
    MatExpansionModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatDialogModule,
    FormsModule,
    MatCheckboxModule
  ],
})
export class InspectionDetailComponent implements OnInit {
  inspection: any;
  inspectionRows: any[] = [];
  mushroomStorageDetails: any;
  currentStorage!: any;
  selectedPhotos: any[] = [];
  markingPhotos: any[] = [];
  palletPhotos: any[] = [];
  selectedPalletPhotoIds: number[] = [];
  selectedQuantityPhotoIds: number[] = [];
  selectedQualityPhotoIds: number[] = [];
  selectedPhotoIds:        number[] = []; // для placement
  selectedMarkingPhotoIds: number[] = []; // для marking
  selectedLoadingPhotoIds: number[] = []; // для loading


  constructor(
    private route: ActivatedRoute,
    private service: InspectionsService,
    private dialog: MatDialog,
    private http: HttpClient,
    private router: Router
    ) {}

  // inspection-detail.component.ts
  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id')!;

    // 1) Инспекция
    this.service.getInspectionById(id).subscribe(ins => {
      this.inspection = ins;
      console.log('quantity_inspections', ins.quantity_inspections);
      console.log('inspectionRows', this.inspectionRows);
      if (ins.quantity_inspections?.length) {
        this.inspectionRows = ins.quantity_inspections[0].boxes;
        // ДОБАВИТЬ: подтягиваем фото
        this.service.getQuantityPhotosByInspectionId(id).subscribe(qPhotos => {
          // прямо в массив first.quantity_inspections
          this.inspection.quantity_inspections[0].photos = qPhotos;
        });
      if (ins.quality_inspections?.length) {
        this.service.getQualityPhotosByInspectionId(id).subscribe(qPhotos => {
          this.inspection.quality_inspections[0].photos = qPhotos;
        });

        this.service.getPalletPhotosByInspectionId(id).subscribe(photos => {
          this.palletPhotos = photos;
        });
      }
      }
    });

    // 2) Размещение
    this.service.getMushroomStorageByInspectionId(id).subscribe(storageData => {
      this.mushroomStorageDetails = storageData;
      // Находим именно тот блок, где inspection === id
      // и сохраняем его в currentStorage
      this.currentStorage =
        storageData.find((s: any) => String(s.inspection) === id)
        || storageData[0]; // fallback, если вдруг
    });

    // 3) Маркировка
    this.service.getMarkingPhotosByInspectionId(id).subscribe(photoData => {
      this.markingPhotos = photoData;
    });

    // … и так далее для остальных разделов …
  }

  currentSection!: 'placement' | 'marking' | 'loading' | 'quantity' | 'quality' | 'pallets';

  openPhotoDialog(photos: any[], template: TemplateRef<any>, section: 'placement'|'marking'|'loading'|'quantity'|'quality'|'pallets') {
    this.selectedPhotos = photos;
    this.currentSection = section;  // This will now accept 'loading'
    this.dialog.open(template, {
      width: '90vw',
      height: '90vh',
      maxWidth: 'none',
      panelClass: 'photo-dialog-panel'
    });
  }

togglePhoto(photo: any, section: 'placement'|'marking'|'loading'|'quantity'|'quality'|'pallets') {
  photo.selected = !photo.selected;
  const id = photo.id;
  let target: number[];
  switch (section) {
    case 'placement': target = this.selectedPhotoIds; break;
    case 'marking':   target = this.selectedMarkingPhotoIds; break;
    case 'loading':   target = this.selectedLoadingPhotoIds; break;
    case 'quantity':  target = this.selectedQuantityPhotoIds; break;
    case 'quality':   target = this.selectedQualityPhotoIds; break;
    case 'pallets':   target = this.selectedPalletPhotoIds; break;
    default:
      return;  // на всякий случай
  }
  if (photo.selected) {
    if (!target.includes(id)) target.push(id);
  } else {
    const idx = target.indexOf(id);
    if (idx > -1) target.splice(idx, 1);
  }
}


exportReport(): void {
  const inspectionId = this.inspection.id;
  const payload = {
    placement_photo_ids: this.selectedPhotoIds,
    marking_photo_ids:   this.selectedMarkingPhotoIds,
    loading_photo_ids:   this.selectedLoadingPhotoIds,
    quantity_photo_ids:  this.selectedQuantityPhotoIds,
    quality_photo_ids:   this.selectedQualityPhotoIds,
    pallet_photo_ids:    this.selectedPalletPhotoIds,  // <-- вот он
  };
  this.http.post(
    `http://localhost:8000/generate-report/${inspectionId}/`,
    payload
  ).subscribe();
}

  saveJobNumber(): void {
    const inspectionId = this.inspection.id;
    const updatedJobNumber = this.inspection.job_number;

    this.http.patch(`http://localhost:8000/api/inspections/${inspectionId}/`, { job_number: updatedJobNumber })
      .subscribe({
        next: () => {
          alert('Номер работы успешно сохранён');
        },
        error: () => {
          alert('Ошибка при сохранении номера работы');
        }
      });
  }

  goBack(): void {
    this.router.navigate(['/']); // или путь к вашей главной странице
  }
}
