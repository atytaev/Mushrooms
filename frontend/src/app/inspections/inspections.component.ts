import { Component, OnInit } from '@angular/core';
import { InspectionsService } from '../http.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

@Component({
  selector: 'app-inspections',
  templateUrl: './inspections.component.html',
  styleUrls: ['./inspections.component.css'],
  standalone: true,
  imports: [CommonModule, FormsModule]
})
export class InspectionsComponent implements OnInit {
  inspections: any[] = [];

  showSettings = false;
  deviceType: 'thermometer' | 'scale' = 'thermometer';

  thermometers: any[] = [];
  scales: any[] = [];

  newThermometer = { info: '', serial: '', calibration_date: '' };
  newScale = { model: '', serial_number: '', calibration_date: '' };

  page = 1;
  pageSize = 20;

  constructor(private inspectionsService: InspectionsService, private router: Router) {}

  ngOnInit(): void {
    this.loadThermometers();
    this.loadScales();
    this.inspectionsService.getInspections().subscribe(data => {
      this.inspections = data.sort((a, b) => new Date(b.inspection_date).getTime() - new Date(a.inspection_date).getTime());
    });
  }

  toggleSettings() {
    this.showSettings = !this.showSettings;
  }

  selectDevice(type: 'thermometer' | 'scale') {
    this.deviceType = type;
  }

  // Thermometers
  loadThermometers() {
    this.inspectionsService.getThermometers().subscribe(data => {
      this.thermometers = data.map(t => ({
        ...t,
        calibration_date: t.calibration_date ? t.calibration_date.split('T')[0] : ''
      }));
    });
  }

  saveThermometer(t: any, index: number) {
    this.inspectionsService.updateThermometer(t.id, t).subscribe(updated => {
      this.thermometers[index] = updated;
      alert('Термометр сохранён');
    });
  }

  deleteThermometer(id: number, index: number) {
    if (!confirm('Удалить этот термометр?')) return;
    this.inspectionsService.deleteThermometer(id).subscribe(() => {
      this.thermometers.splice(index, 1);
    });
  }

  addThermometer() {
    if (!this.newThermometer.info.trim()) {
      alert('Введите информацию о термометре');
      return;
    }
    this.inspectionsService.addThermometer(this.newThermometer).subscribe(newT => {
      newT.calibration_date = newT.calibration_date ? newT.calibration_date.split('T')[0] : '';
      this.thermometers.push(newT);
      this.newThermometer = { info: '', serial: '', calibration_date: '' };
      alert('Термометр добавлен');
    });
  }

  // Scales
  loadScales() {
    this.inspectionsService.getScales().subscribe(data => {
      this.scales = data.map(s => ({
        ...s,
        calibration_date: s.calibration_date ? s.calibration_date.split('T')[0] : ''
      }));
    });
  }

  saveScale(s: any, index: number) {
    this.inspectionsService.updateScale(s.id, s).subscribe(updated => {
      this.scales[index] = updated;
      alert('Весы сохранены');
    });
  }

  deleteScale(id: number, index: number) {
    if (!confirm('Удалить эти весы?')) return;
    this.inspectionsService.deleteScale(id).subscribe(() => {
      this.scales.splice(index, 1);
    });
  }

  addScale() {
    if (!this.newScale.model.trim()) {
      alert('Введите модель весов');
      return;
    }
    this.inspectionsService.addScale(this.newScale).subscribe(newS => {
      newS.calibration_date = newS.calibration_date ? newS.calibration_date.split('T')[0] : '';
      this.scales.push(newS);
      this.newScale = { model: '', serial_number: '', calibration_date: '' };
      alert('Весы добавлены');
    });
  }

  goToDetail(id: number) {
    if (id) this.router.navigate(['/inspections', id]);
  }

  get pagedInspections() {
    const start = (this.page - 1) * this.pageSize;
    return this.inspections.slice(start, start + this.pageSize);
  }

  get totalPages() {
    return Math.ceil(this.inspections.length / this.pageSize);
  }

  changePage(newPage: number) {
    if (newPage >= 1 && newPage <= this.totalPages) {
      this.page = newPage;
    }
  }

}
