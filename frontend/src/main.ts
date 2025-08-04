import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app.component';
import 'moment/locale/ru';
import * as moment from 'moment';

bootstrapApplication(AppComponent, appConfig)
  .catch((err) => console.error(err));
moment.locale('ru');
