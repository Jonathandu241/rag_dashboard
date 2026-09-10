// Miroir de la config Tailwind inline de templates/index.html (non chargé par la page,
// gardé cohérent — cf. AGENTS.md §6). Toute modif ici doit être répercutée dans le <head>.
tailwind.config = {
    darkMode: 'class',
    theme: {
        extend: {
            fontFamily: {
                display: ['Marcellus', 'serif'],
                sans: ['"IBM Plex Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
                mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
            },
            colors: {
                bg: 'var(--bg)',
                surface: 'var(--surface)',
                ink: 'var(--ink)',
                muted: 'var(--muted)',
                line: 'var(--line)',
                accent: 'var(--accent)',
                'accent-hover': 'var(--accent-hover)',
                danger: 'var(--danger)',
            },
            borderRadius: {
                DEFAULT: '2px', sm: '2px', md: '2px', lg: '2px', xl: '2px', '2xl': '2px', full: '2px',
            },
        },
    },
};
