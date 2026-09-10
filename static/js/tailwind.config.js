// Miroir de la config Tailwind inline de templates/index.html (non chargé par la page,
// gardé cohérent - cf. AGENTS.md §6). Toute modif ici doit être répercutée dans le <head>.
tailwind.config = {
    darkMode: 'class',
    theme: {
        extend: {
            fontFamily: {
                display: ['Marcellus', 'serif'],
                sans: ['"Plus Jakarta Sans"', 'sans-serif'],
            },
            colors: {
                goree: {
                    bg: '#0B0D17',
                    surface: '#13172B',
                    card: '#1B203B',
                    border: 'rgba(232, 200, 74, 0.15)',
                    gold: '#E8C84A',
                    goldHover: '#F4D665',
                    accent: '#3B82F6',
                },
            },
        },
    },
};
