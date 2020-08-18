import matplotlib.pyplot as plt
import numpy as np

# Simulated data
sim = True
params = {'zero_dist_prob_neg_exponent': np.array([0.10729586, 0.07788552, 0.07041277, 0.06635601, 0.07057455,
                                                   0.06763991, 0.07160212, 0.06905329, 0.07061137, 0.06996625,
                                                   0.07048626, 0.07022941, 0.06984598, 0.0696896, 0.07032836,
                                                   0.0699152, 0.07002099, 0.07009039, 0.0699626, 0.06979866,
                                                   0.07018182, 0.06985327, 0.07018182, 0.06988241, 0.0699699,
                                                   0.07032103, 0.06980958]),
          'distance_params': {'a_speed': np.array([1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                                                   1., 1., 1., 1., 1., 1., 1., 1., 1., 1.]),
                              'b_speed': np.array([0.1, 0.0767073, 0.04027141, 0.10209761, 0.03487298,
                                                   0.10494273, 0.05107259, 0.07839112, 0.06085629, 0.06903487,
                                                   0.06554816, 0.06713459, 0.06638689, 0.0663373, 0.06646729,
                                                   0.06671372, 0.06667865, 0.06668224, 0.06663151, 0.06645822,
                                                   0.0667462, 0.06666472, 0.06673121, 0.06680948, 0.06674033,
                                                   0.0667658, 0.06685316])},
          'deviation_beta': np.array([0.01, 0.11968821, 0.09604259, 0.08551236, 0.07052792,
                                      0.0713793, 0.0615319, 0.06261857, 0.05893773, 0.05918318,
                                      0.05805835, 0.05769313, 0.0570676, 0.05672674, 0.05686257,
                                      0.05678954, 0.05667511, 0.05656698, 0.05655971, 0.05644663,
                                      0.05645677, 0.05632237, 0.0563739, 0.05643622, 0.05628776,
                                      0.05657747, 0.05635882]),
          'gps_sd': np.array([7., 4.92872616, 3.87786215, 3.44042854, 3.23996016,
                              3.16084098, 3.11632041, 3.1065256, 3.09031081, 3.09402912,
                              3.08902809, 3.0901351, 3.10220608, 3.10209824, 3.10675427,
                              3.10586138, 3.10596888, 3.09484828, 3.09196818, 3.09170729,
                              3.09386452, 3.09040784, 3.09530273, 3.0980217, 3.09172138,
                              3.09175725, 3.09319397])}

# Real data
sim = False
params = {'zero_dist_prob_neg_exponent': np.array([0.10729586, 0.1281544, 0.13308495, 0.13144832, 0.13043959,
                                                   0.12923439, 0.12822586, 0.12823236, 0.1267411, 0.12678561,
                                                   0.12556916, 0.12523896, 0.12405016, 0.12428868, 0.12420296,
                                                   0.12354536, 0.12389771, 0.12373953, 0.12323103, 0.12323103,
                                                   0.12273238, 0.12261277, 0.12328533, 0.12342429, 0.12280424,
                                                   0.1223385, 0.12238612, 0.12316473, 0.12254708, 0.12195876,
                                                   0.12200019, 0.12179921, 0.12171073, 0.12123498, 0.12136386,
                                                   0.12091387, 0.12172842, 0.12168716, 0.12179331, 0.12179921,
                                                   0.12170484]),
          'distance_params': {'a_speed': np.array([1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                                                   1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
                                                   1., 1., 1., 1., 1., 1., 1.]),
                              'b_speed': np.array([0.1, 0.08173396, 0.068604, 0.06132034, 0.05537686,
                                                   0.05233984, 0.04940389, 0.04694194, 0.04497989, 0.04303832,
                                                   0.04187374, 0.04051936, 0.03957976, 0.03871352, 0.0380473,
                                                   0.03756192, 0.03678313, 0.03632466, 0.03584752, 0.0352923,
                                                   0.03461768, 0.03422825, 0.03378692, 0.03338948, 0.03309382,
                                                   0.03270902, 0.03235274, 0.0318603, 0.03163268, 0.03158895,
                                                   0.03131789, 0.0311463, 0.03109447, 0.03104193, 0.03087489,
                                                   0.03060735, 0.03055145, 0.03034871, 0.03013656, 0.02992404,
                                                   0.02973769])},
          'deviation_beta': np.array([0.01, 0.02818749, 0.02385503, 0.02545854, 0.02018395,
                                      0.0231455, 0.02382913, 0.02443883, 0.02509806, 0.02354816,
                                      0.02495815, 0.02388438, 0.02362069, 0.02352102, 0.0236528,
                                      0.02527522, 0.02465651, 0.02582517, 0.02670992, 0.02732478,
                                      0.02610673, 0.02680588, 0.02724215, 0.02755797, 0.02811108,
                                      0.02804, 0.02839625, 0.02721217, 0.02652799, 0.02736853,
                                      0.02666609, 0.02618454, 0.02691635, 0.02769971, 0.0281767,
                                      0.02727637, 0.0289304, 0.02917431, 0.02930129, 0.0292089,
                                      0.0291403]),
          'gps_sd': np.array([7., 6.33172961, 6.00343728, 5.80854799, 5.70506745,
                              5.67235134, 5.65446872, 5.64512832, 5.68740126, 5.62657349,
                              5.63918995, 5.62454592, 5.63282751, 5.63559472, 5.63041187,
                              5.63452732, 5.6201796, 5.61240535, 5.62708555, 5.6301737,
                              5.65555636, 5.67324982, 5.67410078, 5.67802157, 5.68201249,
                              5.6968524, 5.66484459, 5.64393446, 5.65594528, 5.65171204,
                              5.667375, 5.65833597, 5.6693508, 5.63807512, 5.64164608,
                              5.61089823, 5.64349981, 5.68603298, 5.65603741, 5.68718913,
                              5.68845124])}

params = {'zero_dist_prob_neg_exponent': np.array([0.10729586, 0.11067226, 0.11326288, 0.1151559 , 0.11678391,
       0.11804512, 0.11916287, 0.12023674, 0.12119178]), 'distance_params': { 'a_speed': np.array([1., 1., 1., 1., 1., 1., 1., 1., 1.]), 'b_speed': np.array([0.1       , 0.08395189, 0.07369954, 0.06888329, 0.06503641,
       0.06369609, 0.06253557, 0.06137003, 0.0601717 ])}, 'deviation_beta': np.array([0.01      , 0.02224717, 0.01798748, 0.02022946, 0.01426601,
       0.01601389, 0.01872505, 0.01891354, 0.01664812]), 'gps_sd': np.array([7.        , 6.30740206, 5.98001885, 5.82972883, 5.69773159,
       5.63730345, 5.65307138, 5.63926462, 5.62257127])}

params = {'zero_dist_prob_neg_exponent': np.array([0.10729586, 0.11312489, 0.11770446, 0.12067218, 0.12283131]), 'distance_params': {'a_speed': np.array([1., 1., 1., 1., 1.]), 'b_speed': np.array([0.1, 0.11376962, 0.10305018, 0.09747346, 0.09664983])}, 'deviation_beta': np.array([0.01      , 0.07825384, 0.05811105, 0.03816251, 0.03479726]), 'gps_sd': np.array([7., 6.32441576, 6.07446773, 6.48577567, 6.07776872])}

n_iter = len(params['gps_sd'])

fig, axes = plt.subplots(4, 1, sharex=True, figsize=(7, 10))

axes[0].plot(np.arange(n_iter), np.exp(-15 * params['zero_dist_prob_neg_exponent']))
axes[1].plot(np.arange(n_iter), params['distance_params']['b_speed'])
axes[2].plot(np.arange(n_iter), params['deviation_beta'])
axes[3].plot(np.arange(n_iter), params['gps_sd'])

axes[0].set_ylabel(r'$p^0$')
axes[1].set_ylabel(r'$\lambda$')
axes[2].set_ylabel(r'$\beta$')
axes[3].set_ylabel(r'$\sigma_{GPS}$')


if sim:
       line_colour = 'purple'
       axes[0].hlines(0.35, 0, n_iter, colors=line_colour)
       axes[1].hlines(1 / 15, 0, n_iter, colors=line_colour)
       axes[2].hlines(0.05, 0, n_iter, colors=line_colour)
       axes[3].hlines(3, 0, n_iter, colors=line_colour)

plt.tight_layout()
plt.show()
