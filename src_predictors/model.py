import torch


def conv_out_len(W, K, P, S):
    return int(((W - K + 2 * P) / S) + 1)


class model_3DOnco(torch.nn.Module):

    def __init__(self, hidden_dim, seq_len, mode=None, inputs_voc=None):
        super(model_3DOnco, self).__init__()
        self.mode = mode
        if mode is not None:
            if inputs_voc is None:
                raise ValueError("input_voc cannot be None")
            self.seq_feature = torch.nn.Sequential(
                torch.nn.Conv1d(inputs_voc, hidden_dim * 2, stride=4, padding=2, kernel_size=7, bias=False),
                torch.nn.BatchNorm1d(hidden_dim * 2),
                torch.nn.ReLU(inplace=True),
                torch.nn.MaxPool1d(kernel_size=5, stride=2, padding=2),
                torch.nn.Dropout(p=0.5)
            )

        # [batch, bins, seq, seq]
        # [(W−K+2P)/S]+1
        # W = 3000, K = 7, P = 2, S = 4
        self.dist_feature = torch.nn.Sequential(
            torch.nn.Conv2d(1, hidden_dim * 2, stride=4, padding=2, kernel_size=7, bias=False),
            # [batch, hidden_dim*2, seq*, seq*
            torch.nn.BatchNorm2d(hidden_dim * 2),
            torch.nn.ReLU(inplace=True),
            torch.nn.MaxPool2d(kernel_size=5, stride=2, padding=2),  # [batch, bins*, seq*, seq*]
            torch.nn.Dropout()
        )
        out_conv = conv_out_len(W=conv_out_len(W=seq_len, K=7, P=2, S=4),
                                K=5, S=2, P=2)
        # non so la dimensione (da stampare)
        self.dist_linear_2d = torch.nn.Sequential(
            torch.nn.Linear(out_conv, hidden_dim * 4),  # [batch, seq, seq, bins]
            torch.nn.ReLU(inplace=True)
        )
        self.dist_linear_1d = torch.nn.Sequential(
            torch.nn.Linear(hidden_dim * hidden_dim * seq_len, hidden_dim * 4),
            torch.nn.ReLU(inplace=True)
        )
        self.seq_linear = torch.nn.Sequential(
            torch.nn.Linear(out_conv * hidden_dim * 2, hidden_dim * 4),
            torch.nn.ReLU(inplace=True)
        )

        self.classifier = torch.nn.Sequential(
            torch.nn.Linear(hidden_dim * 4, 2),
            torch.nn.ReLU(inplace=True),
            torch.nn.Dropout(),
            torch.nn.Softmax(dim=1)
        )

    def forward(self, x):
        # [feature, batch, vocab, seq_len]
        if self.mode is not None:
            out_seq = self.seq_feature(x[0])
            out_seq = self.seq_linear(out_seq.view(x[0].size(0),-1))

        out_dist = self.dist_feature(
            x[-1].view(x[-1].size(0), 1, x[-1].size(-1), x[-1].size(-1)))  # [batch, vocab, seq, seq]
        out_dist = self.dist_linear_2d(out_dist)  # [batch, vocab, seq, seq]
        out_dist = out_dist.view(out_dist.size(0), -1)  # [batch, seq * seq * vacab]
        out_dist = self.dist_linear_1d(out_dist)

        # reunion
        if self.mode is None:
            out = out_dist.unsqueeze(1)  # [batch, feature, seq_len, vocab]

        else:
            out = out_seq + out_dist.unsqueeze(0)  # [batch, feature, seq_len, vocab]

        out = self.classifier(out.view(out_dist.size(0), -1))

        return out


class MyConvLSTMCell(torch.nn.Module):

    def __init__(self, input_size, hidden_size, kernel_size=3, stride=1, padding=1, conv_type='1D'):
        super(MyConvLSTMCell, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
        if conv_type == '2D':
            self.conv_i_xx = torch.nn.Conv2d(input_size, hidden_size, kernel_size=kernel_size, stride=stride,
                                             padding=padding)
            self.conv_i_hh = torch.nn.Conv2d(hidden_size, hidden_size, kernel_size=kernel_size, stride=stride,
                                             padding=padding,
                                             bias=False)

            self.conv_f_xx = torch.nn.Conv2d(input_size, hidden_size, kernel_size=kernel_size, stride=stride,
                                             padding=padding)
            self.conv_f_hh = torch.nn.Conv2d(hidden_size, hidden_size, kernel_size=kernel_size, stride=stride,
                                             padding=padding,
                                             bias=False)

            self.conv_c_xx = torch.nn.Conv2d(input_size, hidden_size, kernel_size=kernel_size, stride=stride,
                                             padding=padding)
            self.conv_c_hh = torch.nn.Conv2d(hidden_size, hidden_size, kernel_size=kernel_size, stride=stride,
                                             padding=padding,
                                             bias=False)

            self.conv_o_xx = torch.nn.Conv2d(input_size, hidden_size, kernel_size=kernel_size, stride=stride,
                                             padding=padding)
            self.conv_o_hh = torch.nn.Conv2d(hidden_size, hidden_size, kernel_size=kernel_size, stride=stride,
                                             padding=padding,
                                             bias=False)
        elif conv_type == '1D':
            self.conv_i_xx = torch.nn.Conv1d(input_size, hidden_size, kernel_size=kernel_size, stride=stride,
                                             padding=padding)
            self.conv_i_hh = torch.nn.Conv1d(hidden_size, hidden_size, kernel_size=kernel_size, stride=stride,
                                             padding=padding,
                                             bias=False)

            self.conv_f_xx = torch.nn.Conv1d(input_size, hidden_size, kernel_size=kernel_size, stride=stride,
                                             padding=padding)
            self.conv_f_hh = torch.nn.Conv1d(hidden_size, hidden_size, kernel_size=kernel_size, stride=stride,
                                             padding=padding,
                                             bias=False)

            self.conv_c_xx = torch.nn.Conv1d(input_size, hidden_size, kernel_size=kernel_size, stride=stride,
                                             padding=padding)
            self.conv_c_hh = torch.nn.Conv1d(hidden_size, hidden_size, kernel_size=kernel_size, stride=stride,
                                             padding=padding,
                                             bias=False)

            self.conv_o_xx = torch.nn.Conv1d(input_size, hidden_size, kernel_size=kernel_size, stride=stride,
                                             padding=padding)
            self.conv_o_hh = torch.nn.Conv1d(hidden_size, hidden_size, kernel_size=kernel_size, stride=stride,
                                             padding=padding,
                                             bias=False)

        torch.nn.init.xavier_normal_(self.conv_i_xx.weight)
        torch.nn.init.constant_(self.conv_i_xx.bias, 0)
        torch.nn.init.xavier_normal_(self.conv_i_hh.weight)

        torch.nn.init.xavier_normal_(self.conv_f_xx.weight)
        torch.nn.init.constant_(self.conv_f_xx.bias, 0)
        torch.nn.init.xavier_normal_(self.conv_f_hh.weight)

        torch.nn.init.xavier_normal_(self.conv_c_xx.weight)
        torch.nn.init.constant_(self.conv_c_xx.bias, 0)
        torch.nn.init.xavier_normal_(self.conv_c_hh.weight)

        torch.nn.init.xavier_normal_(self.conv_o_xx.weight)
        torch.nn.init.constant_(self.conv_o_xx.bias, 0)
        torch.nn.init.xavier_normal_(self.conv_o_hh.weight)

    def forward(self, x, state):
        if state is None:
            state = (torch.randn(x.size(0), x.size(1), x.size(2), x.size(3)).cuda(),
                     torch.randn(x.size(0), x.size(1), x.size(2), x.size(3)).cuda())
        ht_1, ct_1 = state
        it = torch.sigmoid(self.conv_i_xx(x) + self.conv_i_hh(ht_1))
        ft = torch.sigmoid(self.conv_f_xx(x) + self.conv_f_hh(ht_1))
        ct_tilde = torch.tanh(self.conv_c_xx(x) + self.conv_c_hh(ht_1))
        ct = (ct_tilde * it) + (ct_1 * ft)
        ot = torch.sigmoid(self.conv_o_xx(x) + self.conv_o_hh(ht_1))
        ht = ot * torch.tanh(ct)
        return ht, ct


class attentionLSTM(torch.nn.Module):
    def __init__(self, num_classes=2, hidden_dim=128):
        super(attentionLSTM, self).__init__()
        self.num_classes = num_classes
        self.hidden_dim = hidden_dim

        self.lstm_cell_m = MyConvLSTMCell(1, hidden_dim, conv_type='2D')
        self.avgpool_m = torch.nn.AvgPool2d(7)
        self.classifier_m = torch.nn.Sequential(torch.nn.Dropout(0.7),
                                                torch.nn.Linear(hidden_dim * 9 * 9, self.num_classes))

        self.lstm_cell_s = MyConvLSTMCell(20, hidden_dim, conv_type='1D')
        self.avgpool_s = torch.nn.AvgPool2d(7)
        self.classifier_s = torch.nn.Sequential(torch.nn.Dropout(0.7),
                                                torch.nn.Linear(2 * 9 * 9, self.num_classes))

        self.softmax = torch.nn.Softmax()

    def forward(self, inputVariable):
        # matrix

        matrixes = inputVariable[1].view(inputVariable[1].shape[1],inputVariable[1].shape[0],
                                         1, 64, 64)  # batch x seq x seq
        sequences = inputVariable[0].view(inputVariable[0].shape[1],inputVariable[0].shape[0],
                                          *inputVariable[0].shape[2:])  # batch x 20 x seq

        state = (torch.zeros((matrixes.shape[1], self.hidden_dim, 64, 64)).cuda(),  # vocab x seq x seq
                 torch.zeros((matrixes.shape[1], self.hidden_dim, 64, 64)).cuda())

        for t in range(matrixes.size(0)):  # sui pices
            state = self.lstm_cell_m(matrixes[t], state)

        feats1_matrix = self.avgpool_m(state[1]).view(state[1].size(0), -1)
        feats_matrix = self.classifier_m(feats1_matrix)

        state = (torch.zeros(inputVariable[0].shape[0], self.hidden_dim, 64).cuda(),  # vocab x seq
                 torch.zeros(inputVariable[0].shape[0], self.hidden_dim, 64).cuda())

        for t in range(sequences.size(0)):  # sui pices
            state = self.lstm_cell_s(sequences[t], state)

        feats1_sequence = self.avgpool_s(state[1]).view(state[1].size(0), -1)
        feats_sequence = self.classifier_s(feats1_sequence)
        feats = self.softmax(feats_sequence + feats_matrix)

        return feats  # ripristinare il batch di 1