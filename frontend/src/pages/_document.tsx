import { Html, Head, Main, NextScript } from 'next/document';

export default function Document() {
  return (
    <Html lang="en">
      <Head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
        <title>PathShield — Route Resilience Intelligence</title>
        <meta name="description" content="Urban Mobility Route Resilience Platform - Deep Learning spectrally-blind road healing and topological vulnerability simulations." />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}
