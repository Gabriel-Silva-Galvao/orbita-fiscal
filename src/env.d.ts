declare namespace App {
  interface Locals {
    /** Preenchido pelo middleware com a resposta de GET {API_URL}/auth/sessao. Vazio em demonstração. */
    usuario?: { id: string; email: string; nome?: string; plano?: 'pro' | 'max' };
  }
}
