import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  FraudAlert,
  FraudAlertInput,
  GenerateTransactionsRequest,
  GenerationAccepted,
  PageResponse,
  Transaction,
  TransactionInput,
} from '../models/api.models';

@Injectable({ providedIn: 'root' })
export class FraudMonitorApi {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api';

  generateTransactions(payload: GenerateTransactionsRequest): Observable<GenerationAccepted> {
    return this.http.post<GenerationAccepted>(`${this.baseUrl}/generator/run`, payload);
  }

  getTransactions(page = 1, pageSize = 40, search = ''): Observable<PageResponse<Transaction>> {
    return this.http.get<PageResponse<Transaction>>(`${this.baseUrl}/transactions`, {
      params: this.pageParams(page, pageSize, search),
    });
  }

  getTransaction(id: string): Observable<Transaction> {
    return this.http.get<Transaction>(`${this.baseUrl}/transactions/${encodeURIComponent(id)}`);
  }

  createTransaction(payload: Transaction): Observable<Transaction> {
    return this.http.post<Transaction>(`${this.baseUrl}/transactions`, payload);
  }

  updateTransaction(id: string, payload: TransactionInput): Observable<Transaction> {
    return this.http.put<Transaction>(`${this.baseUrl}/transactions/${encodeURIComponent(id)}`, payload);
  }

  deleteTransaction(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/transactions/${encodeURIComponent(id)}`);
  }

  getFraudAlerts(page = 1, pageSize = 40, search = ''): Observable<PageResponse<FraudAlert>> {
    return this.http.get<PageResponse<FraudAlert>>(`${this.baseUrl}/fraud-alerts`, {
      params: this.pageParams(page, pageSize, search),
    });
  }

  getFraudAlert(transactionId: string, rule: string): Observable<FraudAlert> {
    return this.http.get<FraudAlert>(this.alertUrl(transactionId, rule));
  }

  createFraudAlert(payload: FraudAlert): Observable<FraudAlert> {
    return this.http.post<FraudAlert>(`${this.baseUrl}/fraud-alerts`, payload);
  }

  updateFraudAlert(transactionId: string, rule: string, payload: FraudAlertInput): Observable<FraudAlert> {
    return this.http.put<FraudAlert>(this.alertUrl(transactionId, rule), payload);
  }

  deleteFraudAlert(transactionId: string, rule: string): Observable<void> {
    return this.http.delete<void>(this.alertUrl(transactionId, rule));
  }

  private pageParams(page: number, pageSize: number, search: string): HttpParams {
    let params = new HttpParams().set('page', page).set('page_size', pageSize);
    if (search.trim()) params = params.set('search', search.trim());
    return params;
  }

  private alertUrl(transactionId: string, rule: string): string {
    return `${this.baseUrl}/fraud-alerts/${encodeURIComponent(transactionId)}/${encodeURIComponent(rule)}`;
  }
}
