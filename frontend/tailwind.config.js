/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                slate: {
                    50: '#f8fafc',
                    900: '#0f172a',
                },
                indigo: {
                    600: '#4f46e5',
                    700: '#4338ca',
                }
            }
        },
    },
    plugins: [],
}
