function ragApp() {
    return {
        currentTab: 'corpus',
        sidebarOpen: false,
        stores: [],
        stats: { total_stores: 0, total_docs: 0, storage_enabled: false },
        newStoreName: '',
        loading: false,
        showAllStores: false,
        collapsedStores: {},
        selectedPlaygroundStore: '',
        selectedProfil: 'touriste',
        selectedLangue: 'fr',
        playgroundQuestion: '',
        playgroundAnswer: '',
        playgroundModel: '',
        playgroundLoading: false,
        toast: { show: false, message: '' },
        pdf: { open: false, url: '', title: '' },
        confirmDialog: { open: false, title: '', message: '', confirmLabel: 'Supprimer', onConfirm: null },

        init() {
            this.fetchStores();
            this.$nextTick(() => lucide.createIcons());
        },

        goTo(tab) {
            this.currentTab = tab;
            this.sidebarOpen = false;
            this.$nextTick(() => lucide.createIcons());
        },

        // --- Vue Corpus : pagination des stores ---
        get visibleStores() {
            return this.showAllStores ? this.stores : this.stores.slice(0, 2);
        },

        // --- Vue Documents : repliage des sections ---
        toggleStoreSection(storeName) {
            this.collapsedStores[storeName] = !this.collapsedStores[storeName];
        },
        isCollapsed(storeName) {
            return !!this.collapsedStores[storeName];
        },

        // --- Helpers ---
        formatBytes(n) {
            if (n === null || n === undefined) return '-';
            if (n < 1024) return n + ' o';
            if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' Ko';
            return (n / (1024 * 1024)).toFixed(1) + ' Mo';
        },
        formatDate(iso) {
            if (!iso) return '';
            try {
                return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' });
            } catch (e) {
                return '';
            }
        },
        _docFileUrl(docName) {
            return '/api/documents/file?document_name=' + encodeURIComponent(docName);
        },

        // Ouvre le PDF dans une modale (iframe), sans quitter le dashboard
        openPdf(docName, title) {
            this.pdf.url = this._docFileUrl(docName);
            this.pdf.title = title || 'Document';
            this.pdf.open = true;
            document.body.style.overflow = 'hidden';
        },
        closePdf() {
            this.pdf.open = false;
            this.pdf.url = '';
            document.body.style.overflow = '';
        },
        // Repli : ouvrir dans un onglet séparé
        openDocument(docName) {
            window.open(this._docFileUrl(docName), '_blank', 'noopener');
        },

        showToast(msg) {
            this.toast.message = msg;
            this.toast.show = true;
            setTimeout(() => this.toast.show = false, 3000);
        },

        // --- Modale de confirmation (remplace confirm() natif) ---
        askConfirm(title, message, onConfirm, confirmLabel = 'Supprimer') {
            this.confirmDialog = { open: true, title, message, confirmLabel, onConfirm };
            document.body.style.overflow = 'hidden';
        },
        closeConfirm() {
            this.confirmDialog.open = false;
            this.confirmDialog.onConfirm = null;
            document.body.style.overflow = this.pdf.open ? 'hidden' : '';
        },
        async runConfirm() {
            const action = this.confirmDialog.onConfirm;
            this.closeConfirm();
            if (action) await action();
        },

        // Renvoie true si la session a expiré (401) et redirige vers /login
        _checkAuth(res) {
            if (res.status === 401) {
                window.location.href = '/login';
                return true;
            }
            return false;
        },

        async fetchStores() {
            this.loading = true;
            try {
                const res = await fetch('/api/stores');
                if (this._checkAuth(res)) return;
                const data = await res.json();
                this.stores = data.stores;
                this.stats = data.stats;
                this.$nextTick(() => lucide.createIcons());
            } catch (e) {
                alert("Erreur chargement des stores: " + e.message);
            } finally {
                this.loading = false;
            }
        },

        async createStore() {
            if (!this.newStoreName) return;
            const fd = new FormData();
            fd.append('display_name', this.newStoreName);
            this.loading = true;
            try {
                const res = await fetch('/api/stores/create', { method: 'POST', body: fd });
                if (this._checkAuth(res)) return;
                if (res.ok) {
                    this.newStoreName = '';
                    this.showToast("Store créé avec succès !");
                    await this.fetchStores();
                }
            } catch (e) {
                alert("Erreur création: " + e.message);
            } finally {
                this.loading = false;
            }
        },

        deleteStore(storeName, displayName) {
            this.askConfirm(
                'Supprimer ce store ?',
                `Le store « ${displayName} » et TOUS ses documents indexés seront supprimés définitivement. Cette action est irréversible.`,
                async () => {
                    const fd = new FormData();
                    fd.append('store_name', storeName);
                    this.loading = true;
                    try {
                        const res = await fetch('/api/stores/delete', { method: 'POST', body: fd });
                        if (this._checkAuth(res)) return;
                        this.showToast("Store supprimé.");
                        await this.fetchStores();
                    } catch (e) {
                        alert("Erreur suppression: " + e.message);
                    } finally {
                        this.loading = false;
                    }
                }
            );
        },

        async uploadFile(storeName, event) {
            const file = event.target.files[0];
            if (!file) return;
            const fd = new FormData();
            fd.append('store_name', storeName);
            fd.append('file', file);
            this.loading = true;
            this.showToast(`Upload et indexation de '${file.name}' chez Google en cours...`);
            try {
                const res = await fetch('/api/documents/upload', { method: 'POST', body: fd });
                if (this._checkAuth(res)) return;
                if (res.ok) {
                    this.showToast(`Document '${file.name}' indexé avec succès !`);
                    await this.fetchStores();
                } else {
                    const err = await res.json();
                    alert("Erreur upload: " + err.detail);
                }
            } catch (e) {
                alert("Erreur: " + e.message);
            } finally {
                this.loading = false;
                event.target.value = '';
            }
        },

        deleteDocument(docName, displayName) {
            this.askConfirm(
                'Supprimer ce document ?',
                `« ${displayName || 'Ce document'} » sera retiré du store et sa copie archivée sera supprimée. Cette action est irréversible.`,
                async () => {
                    const fd = new FormData();
                    fd.append('document_name', docName);
                    this.loading = true;
                    try {
                        const res = await fetch('/api/documents/delete', { method: 'POST', body: fd });
                        if (this._checkAuth(res)) return;
                        this.showToast("Document supprimé.");
                        await this.fetchStores();
                    } catch (e) {
                        alert("Erreur: " + e.message);
                    } finally {
                        this.loading = false;
                    }
                }
            );
        },

        async runPlaygroundTest() {
            if (!this.selectedPlaygroundStore || !this.playgroundQuestion) return;
            this.playgroundLoading = true;
            this.playgroundAnswer = '';
            this.playgroundModel = '';
            const fd = new FormData();
            fd.append('store_name', this.selectedPlaygroundStore);
            fd.append('question', this.playgroundQuestion);
            fd.append('profil', this.selectedProfil);
            fd.append('langue', this.selectedLangue);
            try {
                const res = await fetch('/api/playground/test', { method: 'POST', body: fd });
                if (this._checkAuth(res)) return;
                const data = await res.json();
                if (res.ok) {
                    this.playgroundAnswer = data.answer;
                    this.playgroundModel = data.model;
                } else {
                    alert("Erreur test IA: " + data.detail);
                }
            } catch (e) {
                alert("Erreur test IA: " + e.message);
            } finally {
                this.playgroundLoading = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        copyToClipboard(text) {
            navigator.clipboard.writeText(text);
            this.showToast("ID copié dans le presse-papier !");
        }
    };
}
