import type { AppProps } from 'next/app'
import { Toaster } from 'react-hot-toast'
import Layout from '../components/Layout'
import '../styles/globals.css'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <Layout>
      <Component {...pageProps} />
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: '#141c2e',
            color: '#e2e8f0',
            border: '1px solid #1e2d45',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '0.8rem',
          },
        }}
      />
    </Layout>
  )
}
