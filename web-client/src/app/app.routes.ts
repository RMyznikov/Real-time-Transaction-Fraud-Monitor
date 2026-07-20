import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'transactions/new' },
  {
    path: 'transactions/new',
    loadComponent: () =>
      import('./pages/generate-transactions/generate-transactions').then(
        (component) => component.GenerateTransactions,
      ),
  },
  {
    path: 'transactions',
    loadComponent: () =>
      import('./pages/transactions/transactions').then(
        (component) => component.Transactions,
      ),
  },
  {
    path: 'fraud-alerts',
    loadComponent: () =>
      import('./pages/fraud-alerts/fraud-alerts').then(
        (component) => component.FraudAlerts,
      ),
  },
  { path: '**', redirectTo: 'transactions/new' },
];
