function ragApp() {
    return {
        currentTab: 'corpus',
        stores: [],
        stats: { total_stores: 0, total_docs: 0 },
        newStoreName: '',
        loading: false,
        selectedPlaygroundStore: '',
        selectedProfil: 'touriste',
        selectedLangue: 'fr',
        playgroundQuestion: '',
        playgroundAnswer: '',
        playgroundModel: '',
        playgroundLoading: false,
        toast: { show: false, message: '' },

        init() {
            this.fetchStores();
            this.$nextTick(() => lucide.createIcons());
        },

        showToast(msg) {
            this.toast.message = msg;
            this.toast.show = true;
            setTimeout(() => this.toast.show = false, 3000);
        },

        async fetchStores() {
            this.loading = true;
            try {
                const res = await fetch('/api/stores');
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

        async deleteStore(storeName, displayName) {
            if (!confirm(`Confirmer la suppression du store '${displayName}' et de TOUS ses documents ?`)) return;
            const fd = new FormData();
            fd.append('store_name', storeName);
            this.loading = true;
            try {
                await fetch('/api/stores/delete', { method: 'POST', body: fd });
                this.showToast("Store supprimé.");
                await this.fetchStores();
            } catch (e) {
                alert("Erreur suppression: " + e.message);
            } finally {
                this.loading = false;
            }
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

        async deleteDocument(docName) {
            if (!confirm("Supprimer ce document du store ?")) return;
            const fd = new FormData();
            fd.append('document_name', docName);
            this.loading = true;
            try {
                await fetch('/api/documents/delete', { method: 'POST', body: fd });
                this.showToast("Document supprimé.");
                await this.fetchStores();
            } catch (e) {
                alert("Erreur: " + e.message);
            } finally {
                this.loading = false;
            }
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
