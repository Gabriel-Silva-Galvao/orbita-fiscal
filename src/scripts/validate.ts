/** Validações dos formulários de Entrar e Checkout. Só dígitos importam. */
export const digits = (s: string) => s.replace(/\D/g, '');

export const isEmail = (s: string) => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(s.trim());

/** CPF com dígitos verificadores. */
export function isCPF(raw: string) {
  const d = digits(raw);
  if (d.length !== 11 || /^(\d)\1{10}$/.test(d)) return false;
  const calc = (len: number) => {
    let sum = 0;
    for (let i = 0; i < len; i++) sum += Number(d[i]) * (len + 1 - i);
    const r = (sum * 10) % 11;
    return r === 10 ? 0 : r;
  };
  return calc(9) === Number(d[9]) && calc(10) === Number(d[10]);
}

/** CNPJ numérico com dígitos verificadores. */
export function isCNPJ(raw: string) {
  const d = digits(raw);
  if (d.length !== 14 || /^(\d)\1{13}$/.test(d)) return false;
  const calc = (len: number) => {
    const w = len === 12 ? [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2] : [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    const sum = w.reduce((acc, wi, i) => acc + wi * Number(d[i]), 0);
    const r = sum % 11;
    return r < 2 ? 0 : 11 - r;
  };
  return calc(12) === Number(d[12]) && calc(13) === Number(d[13]);
}

/** 000.000.000-00 ou 00.000.000/0000-00, conforme a quantidade de dígitos. */
export function maskDoc(raw: string) {
  const d = digits(raw).slice(0, 14);
  if (d.length <= 11)
    return d.replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d{1,2})$/, '$1-$2');
  return d
    .replace(/(\d{2})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1/$2')
    .replace(/(\d{4})(\d{1,2})$/, '$1-$2');
}

/** Algoritmo de Luhn para o número do cartão. */
export function isCard(raw: string) {
  const d = digits(raw);
  if (d.length < 13 || d.length > 19) return false;
  let sum = 0;
  for (let i = 0; i < d.length; i++) {
    let n = Number(d[d.length - 1 - i]);
    if (i % 2 === 1) {
      n *= 2;
      if (n > 9) n -= 9;
    }
    sum += n;
  }
  return sum % 10 === 0;
}

export const maskCard = (raw: string) => digits(raw).slice(0, 19).replace(/(\d{4})(?=\d)/g, '$1 ');

export const maskExpiry = (raw: string) => {
  const d = digits(raw).slice(0, 4);
  return d.length > 2 ? `${d.slice(0, 2)}/${d.slice(2)}` : d;
};

/** MM/AA no mês atual ou depois. */
export function isExpiry(raw: string, now = new Date()) {
  const d = digits(raw);
  if (d.length !== 4) return false;
  const m = Number(d.slice(0, 2));
  const y = 2000 + Number(d.slice(2));
  if (m < 1 || m > 12) return false;
  return y > now.getFullYear() || (y === now.getFullYear() && m >= now.getMonth() + 1);
}
