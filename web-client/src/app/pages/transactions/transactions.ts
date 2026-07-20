import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { PageEvent } from '@angular/material/paginator';
import { MtxGridColumn, MtxGridModule } from '@ng-matero/extensions/grid';
import { debounceTime, distinctUntilChanged, finalize } from 'rxjs';

import { Transaction } from '../../models/api.models';
import { FraudMonitorApi } from '../../services/fraud-monitor-api';

@Component({
  selector: 'app-transactions',
  imports: [ReactiveFormsModule, MatButtonModule, MatFormFieldModule, MatInputModule, MtxGridModule],
  templateUrl: './transactions.html',
  styleUrl: './transactions.scss',
})
export class Transactions {
  private readonly api = inject(FraudMonitorApi);
  private readonly destroyRef = inject(DestroyRef);

  readonly data = signal<Transaction[]>([]);
  readonly loading = signal(false);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly pageSize = signal(40);
  readonly error = signal('');
  readonly searchControl = new FormControl('', { nonNullable: true });
  readonly columns: MtxGridColumn<Transaction>[] = [
    { header: 'Transaction ID', field: 'transaction_id', width: '275px' },
    { header: 'Account', field: 'account_id', width: '130px' },
    { header: 'Amount', field: 'amount', width: '140px', formatter: (row) => `${Number(row.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })} ${row.currency}` },
    { header: 'Currency', field: 'currency', width: '95px' },
    { header: 'Country', field: 'country', width: '90px' },
    { header: 'Transaction time', field: 'timestamp', type: 'date', typeParameter: { format: 'MMM d, y, HH:mm:ss' }, width: '190px' },
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
      .getTransactions(this.page(), this.pageSize(), this.searchControl.value)
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (response) => {
          this.data.set(response.items);
          this.total.set(response.total);
        },
        error: () => this.error.set('Transactions could not be loaded. Check the API connection and retry.'),
      });
  }
}
