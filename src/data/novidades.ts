/**
 * Novidades mostradas no Portal (aba Novidades), da mais nova para a mais antiga.
 * Hoje ficam aqui, no código: publicar é editar este arquivo e fazer commit.
 * Plano: publicar pelo painel de administração da API. Observação de 24/11/2026: ainda não se
 * sabe se esse painel será integrado.
 * Regra: só fatos que já aconteceram, com data. Nada de promessa.
 */
export type Novidade = {
  id: string;
  data: string; // AAAA-MM-DD
  origem: 'orbita' | 'ias';
  titulo: string;
  texto: string;
  /** Acesso antecipado: aparece para o Max primeiro. */
  max?: boolean;
};

export const ORIGENS = {
  orbita: 'Órbita',
  ias: 'Claude e outras IAs',
} as const;

export const novidades: Novidade[] = [
  {
    id: '2026-11-24-boleto',
    data: '2026-11-24',
    origem: 'orbita',
    titulo: 'Boleto como forma de pagamento',
    texto: 'Além do cartão e do Pix, a assinatura agora pode ser paga por boleto. O acesso começa quando o banco confirma o pagamento, em até 3 dias úteis.',
  },
  {
    id: '2026-11-24-duas-etapas',
    data: '2026-11-24',
    origem: 'orbita',
    titulo: 'Verificação em duas etapas no login',
    texto: 'Todo login agora pede um código de 6 dígitos enviado ao seu e-mail.',
  },
  {
    id: '2026-11-24-marca',
    data: '2026-11-24',
    origem: 'orbita',
    titulo: 'A marca agora é só Órbita',
    texto: 'Mudamos o nome de Órbita Fiscal para Órbita. Sua conta, seu plano e seus dados continuam iguais.',
  },
];
