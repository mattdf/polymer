let workspace_id = null;
var converter = new showdown.Converter();

document.addEventListener("DOMContentLoaded", () => {

    document.getElementById('analyze-tab-btn').hidden = true;

    // Save workspace ID in URL bar
    const wlh = window.location.hash;
    if( wlh != "" && wlh !== undefined ) {
        workspace_id = wlh.slice(1);
        load_repo(workspace_id);
    }
    
    loadWorkspaces();
    loadPrompts();

    async function http_get(path) {
        const response = await fetch(path, {
            method: "GET",
            headers: {"Content-Type": "application/json"}
        });
        if (response.ok) {
            return await response.json();
        }
        throw Error(response);
    }

    async function http_post(path, data) {
        const response = await fetch(path, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data),
        });
        if (response.ok) {
            return await response.json();
        }
        throw Error(response);
    }

    document.getElementById("message-form").addEventListener("submit", async (event) => {
        event.preventDefault();

        const messageInput = document.getElementById("message-input");
        const message = messageInput.value.trim();

        if (!message) return;

        addMessageToChat("You", message);

        messageInput.value = "";
        messageInput.focus();

        const response = await fetch("/message/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
        });

        if (response.ok) {
            const data = await response.json();
            addMessageToChat("OpenAI", data.response);
        } else {
            addMessageToChat("Error", "Failed to get a response.");
        }
    });

    function addMessageToChat(sender, message) {
        const messages = document.getElementById("messages");
        const messageDiv = document.createElement("div");
        messageDiv.className = sender === "You" ? "user-message" : "bot-message";
        messageDiv.innerHTML = `<strong>${sender}:</strong> ${message}`;
        messages.appendChild(messageDiv);
        messages.scrollTop = messages.scrollHeight;
    }

    async function loadPrompts() {        
        const ap = document.getElementById('analyze-prompt');
        for( const [k,v] of Object.entries(await http_get('/prompts')) ) {
            const se = document.createElement('option');
            se.innerHTML = k + (v.description ? ': ' + v.description : '');
            se.setAttribute('value', k);
            ap.appendChild(se);
        }
    }

    async function loadWorkspaces() {
        const ws = document.getElementById('workspaces');
        for( const [k,v] of Object.entries(await http_get('/workspaces')) ) {
            const li = document.createElement('li');
            const b = document.createElement('a');
            b.setAttribute('href', `#${k}`);
            b.innerText = k;
            b.addEventListener('click', (event) => {
                event.preventDefault();
                load_repo(k);
            });
            li.appendChild(b);
            const a = document.createElement('ul');
            for( const [x,y] of Object.entries(v) ) {
                const c = document.createElement('li');
                c.innerText = `${x}: ${y}`
                a.appendChild(c);
            }
            li.appendChild(a);
            ws.appendChild(li);
        }
    }

    async function loadRepoFromEndpoint() {
        const loadingDiv = document.getElementById('loading-container');
        const loadingSpinner = document.getElementById('loading-spinner');


        // Define the keyframes for the animation
        const keyframes = [
            { transform: 'rotate(0deg)' },
            { transform: 'rotate(360deg)' }
        ];

        // Define the animation properties
        const options = {
            duration: 2000,
            iterations: Infinity
        };

        loadingSpinner.style.transformOrigin = 'center';

        // Create the animation
        const animation = loadingSpinner.animate(keyframes, options);
        loadingDiv.style.display = "block";

        try {
            const url = document.getElementById("list-url-input").value;
            const x = await http_post('/repo.clone', { url: url });
            workspace_id = x.workspace_id;
            window.location.hash = x.workspace_id;
            console.log(x.data)
            displayList(x.data.items);
        } catch (error) {
            alert("Error: " + error.message);
        }

        loadingDiv.style.display = "none";
        animation.pause();
    }

    function displayList(tree, container = null) {
        if (!container) {
            container = document.getElementById("list-container");
        }        

        container.innerHTML = "";

        const ulElement = document.createElement("ul");
        container.appendChild(ulElement);

        tree.forEach((item) => {
            const liElement = document.createElement("li");

            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.onchange = function () {
                    if (item.type === "directory") {
                    checkAllChildren(liElement, checkbox.checked);
                }
            };
            liElement.appendChild(checkbox);

            const label = document.createElement("label");
            label.textContent = item.name;

            const icon = document.createElement("span");
            icon.className = item.type === "directory" ? "folder-icon" : "file-icon";
            liElement.classList.add("data-item-" + item.type)
            label.prepend(icon);

            label.onclick = function () {
                if (item.type === "directory") {
                    toggleNestedListVisibility(liElement);
                }
            };
            liElement.appendChild(label);
            ulElement.appendChild(liElement);

            if (item.type === "directory" && item.children && item.children.length > 0) {
                const nestedContainer = document.createElement("div");
                // nestedContainer.classList.add("hidden"); // Add the "hidden" class by default
                liElement.appendChild(nestedContainer);
                displayList(item.children, nestedContainer);
            }
        });
    }

    async function load_repo(name) {    
        const response = await fetch("/repo/" + name, {
            method: "GET",
            headers: {"Content-Type": "application/json"}
        });        
    
        if (response.ok) {
            const x = await response.json();
            displayList(x.data.items);
            workspace_id = name;
            window.location.hash = x.workspace_id;
        } else {
            alert("Failed to load the list from the endpoint.");
        }
    }

    function displayAnalysisResult(result, container = null) {
        if (!container) {
            container = document.getElementById("analysis-results");
        }

        container.innerHTML = "";

        const ulElement = document.createElement("ul");
        container.appendChild(ulElement);

        result.forEach((item) => {
            const liElement = document.createElement("li");

            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.checked = true;
            checkbox.value = '' + item.data[0] + ',' + item.data[1];
            checkbox.onchange = function () {
                if (item.type === "contract") {
                    checkAllChildren(liElement, checkbox.checked);
                }
            };
            liElement.appendChild(checkbox);

            const label = document.createElement("label");
            label.textContent = item.name;

            const icon = document.createElement("span");
            if (item.type === "contract")    {
                icon.className = "contract-icon";
            }
            if (item.type === "function")    {
                icon.className = "function-icon";
            }
            if (item.type === "modifier")    {
                icon.className = "gear-icon";
            }
            if (item.type === "event")    {
                icon.className = "event-icon";
            }
            if (item.type === "type")    {
                icon.className = "info-icon";
            }
            liElement.classList.add("data-item-" + item.type)
            label.prepend(icon);

            label.onclick = function () {
                if (item.type === "contract") {
                    toggleNestedListVisibility(liElement);
                }
                if (item.type !== "contract") {
                    location.hash = "#" + item.data[0] + "-" + item.data[1];
                }
            };
            liElement.appendChild(label);

            ulElement.appendChild(liElement);

            if (item.type === "contract" && item.children && item.children.length > 0) {
                const nestedContainer = document.createElement("div");
                // nestedContainer.classList.add("hidden"); // Add the "hidden" class by default
                liElement.appendChild(nestedContainer);
                displayAnalysisResult(item.children, nestedContainer);
            }
        });
    }


    function toggleNestedListVisibility(element) {
        const nestedContainer = element.querySelector("div");
        const nestedSpan = element.querySelector("span");
        if (nestedContainer) {
            nestedContainer.classList.toggle("hidden");
            nestedSpan.classList.toggle("folder-open-icon");
            nestedSpan.classList.toggle("folder-icon");
        }
    }
    function checkAllChildren(element, checked) {
        const checkboxes = element.querySelectorAll("input[type=checkbox]");
        checkboxes.forEach((checkbox) => {
            checkbox.checked = checked;
        });
    }

    function collectCheckedFiles(container = document.getElementById("list-container"), path = []) {
        const checkedFiles = [];
        const ulElement = container.querySelector("ul");

        ulElement.childNodes.forEach((liElement) => {
            const checkbox = liElement.querySelector("input[type='checkbox']");
            const label = liElement.querySelector("label");
            const name = label.textContent;

            if (checkbox.checked && liElement.classList.contains("data-item-file"))     {
                const fullPath = [...path, name].join("/");
                checkedFiles.push(fullPath);
            }

            const nestedContainer = liElement.querySelector("div");
            if (nestedContainer) {
                const nestedPath = [...path, name];
                const nestedCheckedFiles = collectCheckedFiles(nestedContainer, nestedPath);
                checkedFiles.push(...nestedCheckedFiles);
            }
        });

        return checkedFiles;
    }

    async function sendCheckedFiles() {
        if( workspace_id === null ) {
            alert('No pipeline id!');
            return;
        }
        const checkedFiles = collectCheckedFiles();
        if( checkedFiles.length == 0 ) {
            return;
        }

        const result = await http_post("/source/" + workspace_id, { files: checkedFiles });
        const contracts = result.contracts;
        const code = result.lines;

        displayAnalysisResult(contracts.items);

        document.getElementById("code-block").textContent = code;
        Prism.highlightAllUnder(document.getElementById("code-editor"));

        toggleTabVisibility("analyze-tab");
        toggleTabVisibilityLeft("code-tab");

        document.getElementById('analyze-tab-btn').hidden = false;
        return result;
    }

    function toggleTabVisibility(tabId) {
        const loadTab = document.getElementById("load-tab");
        const analyzeTab = document.getElementById("analyze-tab");
        const loadTabBtn = document.getElementById("load-tab-btn");
        const analyzeTabBtn = document.getElementById("analyze-tab-btn");

        if (tabId === "load-tab") {
            loadTab.style.display = "block";
            analyzeTab.style.display = "none";
            loadTabBtn.classList.add("active-tab");
            analyzeTabBtn.classList.remove("active-tab");
        } else if (tabId === "analyze-tab") {
            loadTab.style.display = "none";
            analyzeTab.style.display = "block";
            loadTabBtn.classList.remove("active-tab");
            analyzeTabBtn.classList.add("active-tab");
        }
    }

    function toggleTabVisibilityLeft(tabId) {
        const chatTab = document.getElementById("chat-tab");
        const workspacesTab = document.getElementById("workspaces-tab");
        const codeTab = document.getElementById("code-tab");
        const analTab = document.getElementById("analysis-tab");
        const chatTabBtn = document.getElementById("chat-tab-btn");
        const workspacesTabBtn = document.getElementById("workspaces-tab-btn");
        const codeTabBtn = document.getElementById("code-tab-btn");
        const analTabBtn = document.getElementById("analysis-tab-btn");

        if (tabId === "chat-tab") {
            chatTab.style.display = "flex";
            codeTab.style.display = "none";
            analTab.style.display = "none";
            workspacesTab.style.display = "none";
            chatTabBtn.classList.add("active-tab");
            codeTabBtn.classList.remove("active-tab");
            analTabBtn.classList.remove("active-tab");
            workspacesTabBtn.classList.remove("active-tab");
        } else if (tabId === "code-tab") {
            chatTab.style.display = "none";
            codeTab.style.display = "flex";
            analTab.style.display = "none";
            workspacesTab.style.display = "none";
            chatTabBtn.classList.remove("active-tab");
            codeTabBtn.classList.add("active-tab");
            analTabBtn.classList.remove("active-tab");
            workspacesTabBtn.classList.remove("active-tab");
        } else if( tabId == 'analysis-tab' ) {
            chatTab.style.display = "none";
            codeTab.style.display = "none";
            analTab.style.display = "flex";
            workspacesTab.style.display = "none";
            chatTabBtn.classList.remove("active-tab");
            codeTabBtn.classList.remove("active-tab");
            analTabBtn.classList.add("active-tab");
            workspacesTabBtn.classList.remove("active-tab");
        } else if( tabId == 'workspaces-tab' ) {
            chatTab.style.display = "none";
            codeTab.style.display = "none";
            analTab.style.display = "none";
            workspacesTab.style.display = "flex";
            chatTabBtn.classList.remove("active-tab");
            codeTabBtn.classList.remove("active-tab");
            analTabBtn.classList.remove("active-tab");
            workspacesTabBtn.classList.add("active-tab");
        }
    }

    function collectSelectedLines(container = document.getElementById("analysis-results")) {
        const checkedFiles = [];
        const ulElement = container.querySelector("ul");

        ulElement.childNodes.forEach((liElement) => {
            const checkbox = liElement.querySelector("input[type='checkbox']");

            if (checkbox.checked) {
                checkedFiles.push(checkbox.value);
            }

            const nestedContainer = liElement.querySelector("div");
            if (nestedContainer) {
                checkedFiles.push(...collectCheckedFiles(nestedContainer));
            }
        });

        return checkedFiles;
    }

    // https://stackoverflow.com/questions/4810841/pretty-print-json-using-javascript
    // https://jsfiddle.net/KJQ9K/554/
    function syntaxHighlight(json) {
        json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
            var cls = 'number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'key';
                } else {
                    cls = 'string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'boolean';
            } else if (/null/.test(match)) {
                cls = 'null';
            }
            return '<span class="' + cls + '">' + match + '</span>';
        });
    }

    function addAnalysis(result)
    {        
        if( document.getElementById(result.cid) ) {
            return;
        }

        console.log(result);

        const e = document.createElement('div');
        e.setAttribute('id', result.cid);
        e.classList.add("res-output");

        const f = document.createElement('div');
        f.innerHTML = converter.makeHtml(result.result.choices[0].text);
        e.appendChild(f);

        if( result.run ) {
            e.appendChild(document.createElement('hr'));
            const g = document.createElement('pre');
            g.innerHTML = syntaxHighlight(JSON.stringify(result.run[0][6], undefined, 4));
            e.appendChild(g);
        }        

        let append_to;
        if( result.ctx.parent_cid ) {
            append_to = document.getElementById(result.ctx.parent_cid);
        }
        if( append_to === undefined ) {
            append_to = document.getElementById('analysis-tab-outputs');
        }
        append_to.appendChild(e);
    }

    async function sendAnalyzeSelection() {
        addAnalysis(await http_post("/analyze/" + workspace_id, {
            prompt: document.getElementById('analyze-prompt').value,
            files: collectCheckedFiles(),
            lines: collectSelectedLines()
        }));
        toggleTabVisibilityLeft("analysis-tab");
    }

    document.getElementById("load-tab-btn").addEventListener("click", (event) => {
        event.preventDefault();
        toggleTabVisibility("load-tab");
    });

    document.getElementById("analyze-tab-btn").addEventListener("click", (event) => {
        event.preventDefault();
        toggleTabVisibility("analyze-tab");
    });

    document.getElementById("chat-tab-btn").addEventListener("click", (event) => {
        event.preventDefault();
        toggleTabVisibilityLeft("chat-tab");
    });

    document.getElementById("analysis-tab-btn").addEventListener("click", (event) => {
        event.preventDefault();
        toggleTabVisibilityLeft("analysis-tab");
    });

    document.getElementById("code-tab-btn").addEventListener("click", (event) => {
        event.preventDefault();
        toggleTabVisibilityLeft("code-tab");
    });

    document.getElementById("workspaces-tab-btn").addEventListener("click", (event) => {
        event.preventDefault();
        toggleTabVisibilityLeft("workspaces-tab");
    });

    document.getElementById("load-list-btn").addEventListener("click", (event) => {
        event.preventDefault();
        loadRepoFromEndpoint();
    });

    document.getElementById("analyze-button").addEventListener("click", (event) => {
        event.preventDefault();
        sendCheckedFiles();
    });

    document.getElementById("analyze-btn").addEventListener("click", (event) => {
        event.preventDefault();
        sendAnalyzeSelection();
    });

});
