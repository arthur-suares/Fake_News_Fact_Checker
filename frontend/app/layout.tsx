import type { Metadata, Viewport } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Verifica — Verificação de Notícias',
  description:
    'Cole uma notícia, envie uma imagem e receba uma análise de veracidade com fontes e classificação.',
}

export const viewport: Viewport = {
  colorScheme: 'light',
  themeColor: '#6d28d9',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="pt-BR" className="light">
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}
