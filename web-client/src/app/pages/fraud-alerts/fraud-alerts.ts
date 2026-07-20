import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { PageEvent } from '@angular/material/paginator';
import { MtxGridColumn, MtxGridModule } from '@ng-matero/extensions/grid';
import { debounceTime, distinctUntilChanged, finalize } from 'rxjs';

import { FraudAlert } from '../../models/api.models';
import { FraudMonitorApi } from '../../services/fraud-monitor-api';

@Component({
  selector: 'app-fraud-alerts',
  imports: [ReactiveFormsModule, MatButtonModule, MatFormFieldModule, MatInputModule, MtxGridModule],
  templateUrl: './fraud-alerts.html',
  styleUrl: './fraud-alerts.scss',
})
export class FraudAlerts {
  private readonly api = inject(FraudMonitorApi);
  private readonly destroyRef = inject(DestroyRef);

  readonly data = signal<FraudAlert[]>([]);
  readonly loading = signal(false);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly pageSize = signal(40);
  readonly error = signal('');
  readonly searchControl = new FormControl('', { nonNullable: true });
  readonly columns: MtxGridColumn<FraudAlert>[] = [
    { header: 'Transaction ID', field: 'transaction_id', width: '275px' },
    { header: 'Account', field: 'account_id', width: '140px' },
    { header: 'Detection rule', field: 'rule', type: 'tag', width: '180px', tag: { HIGH_AMOUNT: { text: 'HIGH AMOUNT', color: '#fff0e8' } } },
    { header: 'Risk score', field: 'risk_score', type: 'number', width: '120px', formatter: (row) => `${row.risk_score} / 100` },
    { header: 'Created at', field: 'created_at', type: 'date', typeParameter: { format: 'MMM d, y, HH:mm:ss' }, width: '210px' },
  ];

  constructor() {
    this.searchControl.valueChanges
      .pipe(debounceTime(350), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        this.page.set(1);
        this.load();
      });
    this.load();
  }

  onPage(event: PageEvent): void {
    this.page.set(event.pageIndex + 1);
    this.pageSize.set(event.pageSize);
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set('');
    this.api
      .getFraudAlerts(this.page(), this.pageSize(), this.searchControl.value)
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (response) => {
          this.data.set(response.items);
          this.total.set(response.total);
        },
        error: () => this.error.set('Fraud alerts could not be loaded. Check the API connection and retry.'),
      });
  }
}
