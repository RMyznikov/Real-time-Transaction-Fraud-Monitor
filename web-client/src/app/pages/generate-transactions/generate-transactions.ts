import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { finalize } from 'rxjs';

import { FraudMonitorApi } from '../../services/fraud-monitor-api';
import { GenerationSuccessDialog } from './generation-success-dialog';

@Component({
  selector: 'app-generate-transactions',
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './generate-transactions.html',
  styleUrl: './generate-transactions.scss',
})
export class GenerateTransactions {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(FraudMonitorApi);
  private readonly dialog = inject(MatDialog);

  readonly submitting = signal(false);
  readonly error = signal('');
  readonly form = this.fb.nonNullable.group({
    valid_count: [10_000, [Validators.required, Validators.min(0), Validators.max(100_000)]],
    invalid_count: [10_000, [Validators.required, Validators.min(0), Validators.max(100_000)]],
    fraud_count: [10_000, [Validators.required, Validators.min(0), Validators.max(100_000)]],
  });

  get total(): number {
    const value = this.form.getRawValue();
    return value.valid_count + value.invalid_count + value.fraud_count;
  }

  submit(): void {
    if (this.form.invalid || this.submitting()) {
      this.form.markAllAsTouched();
      return;
    }

    this.error.set('');
    this.submitting.set(true);
    this.api
      .generateTransactions(this.form.getRawValue())
      .pipe(finalize(() => this.submitting.set(false)))
      .subscribe({
        next: (result) => this.dialog.open(GenerationSuccessDialog, { data: result }),
        error: () => this.error.set('The generation request could not be submitted. Check the API connection and try again.'),
      });
  }
}
