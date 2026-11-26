declare namespace App {
  interface Locals {
    /** Preenchido pelo middleware com a resposta de GET {API_URL}/auth/sessao. Vazio em demonstração. */
    usuario?: { id: string; email: string; nome?: string; plano?: 'bronze' | 'prata' | 'ouro' };
    /** Item 33: plano atual (GET {API_URL}/billing/plano), preenchido nas rotas de compra e de upgrade. */
    planoAtual?: { plano: 'bronze' | 'prata' | 'ouro' | null; status_acesso: string | null; tem_acesso: boolean };
  }
}
