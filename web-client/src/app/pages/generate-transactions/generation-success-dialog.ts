import { Component, inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';

import { GenerationAccepted } from '../../models/api.models';

@Component({
  selector: 'app-generation-success-dialog',
  imports: [MatButtonModule, MatDialogModule],
  template: `
    <div class="success-mark">✓</div>
    <h2 mat-dialog-title>Generation started</h2>
    <mat-dialog-content>
      {{ data.transaction_count.toLocaleString() }} transactions were accepted and will be added to the outbox in the background.
    </mat-dialog-content>
    <mat-dialog-actions align="end"><button mat-flat-button mat-dialog-close>Done</button></mat-dialog-actions>
  `,
  styles: [`
    :host { display: block; padding-top: 22px; text-align: center; }
    .success-mark { display: grid; width: 54px; height: 54px; margin: 0 auto 4px; place-items: center; border-radius: 50%; background: #e8f8f2; color: #15936a; font-size: 27px; font-weight: 800; }
    h2 { text-align: center; }
    mat-dialog-content { max-width: 390px; color: #667287; line-height: 1.55; }
    mat-dialog-actions { padding: 12px 24px 22px; }
  `],
})
export class GenerationSuccessDialog {
  readonly data = inject<GenerationAccepted>(MAT_DIALOG_DATA);
}
